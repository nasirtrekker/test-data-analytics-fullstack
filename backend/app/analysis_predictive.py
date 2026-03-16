"""Predictive modeling with uncertainty quantification and explainability.

Problem framing (Honest Approach — No Leakage):
  Target  : engagement_rate = (likes + comments + shares) / views
  Inputs  : ONLY pre-publication context (title, category, publish_date)
  Rationale: Model what we can predict BEFORE publication happens.
             Post-publication factors (content virality, recommendation, etc.)
             are NOT available pre-publication, so they're not included.

Leakage prevention:
1. ZERO engagement metrics used as features — pure pre-publication context
2. Dual split by video_id + publish_date ordering: isolate entities and avoid look-ahead
3. Target encoding (if used) fitted on train set only
4. Honest assessment: expect low R² since engagement is unpredictable pre-publication
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

XGBOOST_AVAILABLE = False
try:
    from xgboost import XGBRegressor

    XGBOOST_AVAILABLE = True
except ImportError:
    pass

logger = logging.getLogger(__name__)

# MLflow tracking (optional, graceful degradation)
try:
    import mlflow

    MLFLOW_AVAILABLE = True
    MLFLOW_TRACKING_ENABLED = bool(os.getenv("MLFLOW_TRACKING_URI"))
except ImportError:
    logger.info("MLflow not installed — tracking disabled.")
    MLFLOW_AVAILABLE = False
    MLFLOW_TRACKING_ENABLED = False

MAPIE_AVAILABLE = False
MAPIE_API = "none"
try:
    from mapie.regression import MapieRegressor

    MAPIE_AVAILABLE = True
    MAPIE_API = "legacy"
except Exception:
    try:
        from mapie.regression import CrossConformalRegressor

        MAPIE_AVAILABLE = True
        MAPIE_API = "cross_conformal"
    except Exception:
        logger.warning("MAPIE not available — conformal prediction disabled.")
        MAPIE_AVAILABLE = False
        MAPIE_API = "none"


@dataclass(frozen=True)
class PredictiveArtifacts:
    model: Any
    qhat: float
    alpha: float
    metrics: dict
    feature_importances: list[dict]
    diagnostics: dict
    shap_summary: dict


# Pre-publication features ONLY — no engagement metrics to avoid leakage
# These represent information available BEFORE the video is published
EARLY_FEATURES = [
    "title_length",
    "avg_word_length",
    "title_upper_ratio",
    "publish_year",
    "month_sin",
    "month_cos",
    "dow_sin",
    "dow_cos",
]
PRE_PUB_NUMERIC = EARLY_FEATURES  # Redundant naming kept for compatibility
SAFE_NUMERIC_FEATURES = EARLY_FEATURES
SAFE_CATEGORICAL_FEATURES = ["category", "thumbnail_style"]
TEXT_FEATURE = "title_raw"  # used for TF-IDF bigrams in preprocessor
FORBIDDEN_LEAKAGE_FEATURES = {
    "engagement_rate",
    "engagement_ratio",
    "like_rate",
    "comment_rate",
    "share_rate",
    "likes",
    "comments",
    "shares",
    "views",
}


def _safe_divide(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    den = np.where(np.abs(den) < 1e-12, np.nan, den)
    out = num / den
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


def _smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    # Returns sMAPE as a percentage in [0, 200].
    num = np.abs(y_pred - y_true)
    den = np.abs(y_true) + np.abs(y_pred)
    return float(np.mean(_safe_divide(2.0 * num, den)) * 100.0)


def _maape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    # When y_true=0, APE is undefined; use arctan(inf)=π/2 (maximum penalty).
    with np.errstate(divide="ignore", invalid="ignore"):
        ape = np.abs((y_pred - y_true) / y_true)
    ape = np.where(np.isfinite(ape), ape, np.inf)
    return float(np.mean(np.arctan(ape)))


def _wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    num = np.sum(np.abs(y_true - y_pred))
    den = np.sum(np.abs(y_true))
    if den < 1e-12:
        return 0.0
    return float(num / den)


def _winkler_score(
    y_true: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    alpha: float,
) -> float:
    """Winkler Score — penalises both width and coverage failures.

    WS = (u - l) + (2/α)(l - y)·𝟙[y < l] + (2/α)(y - u)·𝟙[y > u]
    Lower is better. A narrow, well-calibrated interval scores near its width.
    """
    width = upper - lower
    penalty_low = np.where(y_true < lower, (2.0 / alpha) * (lower - y_true), 0.0)
    penalty_high = np.where(y_true > upper, (2.0 / alpha) * (y_true - upper), 0.0)
    return float(np.mean(width + penalty_low + penalty_high))


def _crps_pinball(
    y_true: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    alpha: float,
) -> float:
    """Distribution-free CRPS for conformal prediction intervals via pinball loss.

    Conformal prediction produces quantile forecasts at levels q_low=α/2 and
    q_high=1-α/2.  CRPS is the sum of their pinball (quantile) losses:

      ρ_q(y, f) = (y - f)·q      if y ≥ f
                  (f - y)·(1-q)  if y < f

      CRPS = ρ_{α/2}(y, lower) + ρ_{1-α/2}(y, upper)

    No distributional assumption needed — valid for any conformal interval.
    Lower is better; equals 0 only for a perfect point forecast at the target.
    """
    q_low = alpha / 2.0
    q_high = 1.0 - alpha / 2.0

    err_low = y_true - lower
    pb_low = np.where(err_low >= 0, q_low * err_low, (q_low - 1.0) * err_low)

    err_high = y_true - upper
    pb_high = np.where(err_high >= 0, q_high * err_high, (q_high - 1.0) * err_high)

    return float(np.mean(pb_low + pb_high))


def _build_prepub_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract pre-publication features only (NO engagement metrics).

    Constructs features that would be available BEFORE a video is published,
    completely avoiding any data leakage from engagement metrics.
    """
    out = pd.DataFrame(index=df.index)

    # ─ Pre-publication temporal features ─
    dates = pd.to_datetime(
        df.get("publish_date", pd.Series(dtype=str)), errors="coerce"
    )
    publish_month = dates.dt.month.fillna(1).astype(float)
    publish_weekday = dates.dt.weekday.fillna(0).astype(float)

    titles = df.get("title", pd.Series("", index=df.index)).astype(str).fillna("")
    title_length = titles.str.len().astype(float)
    title_words = titles.str.split().str.len().fillna(1).clip(lower=1).astype(float)

    out["title_length"] = title_length
    out["avg_word_length"] = title_length / title_words
    out["title_upper_ratio"] = titles.str.count(r"[A-Z]") / title_length.clip(lower=1)
    out["publish_year"] = dates.dt.year.fillna(2023).astype(float)
    out["month_sin"] = np.sin(2 * np.pi * publish_month / 12)
    out["month_cos"] = np.cos(2 * np.pi * publish_month / 12)
    out["dow_sin"] = np.sin(2 * np.pi * publish_weekday / 7)
    out["dow_cos"] = np.cos(2 * np.pi * publish_weekday / 7)

    # ─ Categorical features ─
    out["category"] = df.get("category", "unknown").astype(str).fillna("unknown")
    out["thumbnail_style"] = (
        df.get("thumbnail_style", "unknown").astype(str).fillna("unknown")
    )

    # ─ Title text ─
    out["title_raw"] = titles.values

    return out


def _select_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Extract features for predictive modeling (PRE-PUBLICATION CONTEXT ONLY).

    Returns a DataFrame with pre-publication features, indexed like df.
    NO engagement metrics are included — this prevents all leakage.
    """
    return _build_prepub_features(df)


def _assert_no_leakage_features(X: pd.DataFrame) -> None:
    """Fail fast if feature frame contains known leakage-prone columns."""
    used = set(X.columns)
    forbidden_used = sorted(FORBIDDEN_LEAKAGE_FEATURES.intersection(used))
    if forbidden_used:
        raise ValueError(
            "Leakage-prone features detected in predictive feature frame: "
            f"{forbidden_used}. Remove target components and post-publication metrics."
        )


def _videoid_temporal_split(
    X: pd.DataFrame,
    y: pd.Series,
    dates: pd.Series,
    video_ids: pd.Series,
    test_size: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Backward-compatible two-way split by video_id groups + temporal ordering."""
    order = dates.sort_values(kind="mergesort").index
    Xo = X.loc[order].reset_index(drop=True)
    yo = y.loc[order].reset_index(drop=True)
    video_ids_o = video_ids.loc[order].reset_index(drop=True)

    unique_ids = video_ids_o.drop_duplicates().values
    n_videos = len(unique_ids)
    n_test_videos = max(1, int(round(n_videos * test_size)))
    split_point = n_videos - n_test_videos

    train_ids = set(unique_ids[:split_point])
    test_ids = set(unique_ids[split_point:])

    train_mask = video_ids_o.isin(train_ids)
    test_mask = video_ids_o.isin(test_ids)

    return (
        Xo[train_mask].reset_index(drop=True),
        Xo[test_mask].reset_index(drop=True),
        yo[train_mask].reset_index(drop=True),
        yo[test_mask].reset_index(drop=True),
    )


def _videoid_temporal_split_train_val_test(
    X: pd.DataFrame,
    y: pd.Series,
    dates: pd.Series,
    video_ids: pd.Series,
    val_size: float,
    test_size: float,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.Series,
    pd.Series,
    pd.Series,
]:
    """Three-way split by video_id groups with temporal ordering.

    Ordering is strictly chronological by publish_date:
    oldest -> train, middle -> val, newest -> test.
    """
    order = dates.sort_values(kind="mergesort").index
    Xo = X.loc[order].reset_index(drop=True)
    yo = y.loc[order].reset_index(drop=True)
    video_ids_o = video_ids.loc[order].reset_index(drop=True)

    unique_ids = video_ids_o.drop_duplicates().values
    n_videos = len(unique_ids)

    n_test = max(1, int(round(n_videos * test_size)))
    n_val = max(1, int(round(n_videos * val_size)))
    if n_test + n_val >= n_videos:
        n_test = max(1, n_videos // 5)
        n_val = max(1, n_videos // 5)
    n_train = max(1, n_videos - n_val - n_test)

    train_ids = set(unique_ids[:n_train])
    val_ids = set(unique_ids[n_train : n_train + n_val])
    test_ids = set(unique_ids[n_train + n_val :])

    train_mask = video_ids_o.isin(train_ids)
    val_mask = video_ids_o.isin(val_ids)
    test_mask = video_ids_o.isin(test_ids)

    return (
        Xo[train_mask].reset_index(drop=True),
        Xo[val_mask].reset_index(drop=True),
        Xo[test_mask].reset_index(drop=True),
        yo[train_mask].reset_index(drop=True),
        yo[val_mask].reset_index(drop=True),
        yo[test_mask].reset_index(drop=True),
    )


def _time_series_cv(n_samples: int) -> TimeSeriesSplit:
    # Always use TimeSeriesSplit to preserve temporal ordering inside MAPIE CV.
    # A plain int cv=k would trigger random KFold, violating temporal guarantees.
    n_splits = min(5, max(2, n_samples // 60))
    return TimeSeriesSplit(n_splits=n_splits)


def _extract_interval_bounds(
    pred_intervals: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Handle MAPIE interval output shapes across versions."""
    arr = np.asarray(pred_intervals)
    if arr.ndim == 3:
        # Common MAPIE shape: (n_samples, 2, n_alpha)
        lower = arr[:, 0, 0]
        upper = arr[:, 1, 0]
        return lower, upper
    if arr.ndim == 2 and arr.shape[1] == 2:
        # Alternate shape: (n_samples, 2)
        lower = arr[:, 0]
        upper = arr[:, 1]
        return lower, upper
    raise ValueError(f"Unsupported MAPIE interval output shape: {arr.shape}")


def _build_model(random_state: int) -> Pipeline:
    """Build the best-performing pipeline: StandardScaler + OHE + TF-IDF + RF (or XGBoost).

    Hyperparameters are those found by RandomizedSearchCV in the notebook
    (TimeSeriesSplit, 40 iters for RF / 50 for XGBoost).
    """
    numeric = SAFE_NUMERIC_FEATURES
    categorical = SAFE_CATEGORICAL_FEATURES

    pre = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical,
            ),
            (
                "tfidf",
                TfidfVectorizer(max_features=50, ngram_range=(1, 2)),
                TEXT_FEATURE,
            ),
        ]
    )

    if XGBOOST_AVAILABLE:
        estimator = XGBRegressor(
            n_estimators=387,
            max_depth=5,
            learning_rate=0.024,
            subsample=0.914,
            colsample_bytree=0.806,
            min_child_weight=12,
            gamma=0.0035,
            reg_alpha=0.110,
            reg_lambda=1.412,
            tree_method="hist",
            random_state=random_state,
            n_jobs=-1,
            verbosity=0,
        )
    else:
        estimator = RandomForestRegressor(
            n_estimators=585,
            max_depth=9,
            min_samples_leaf=14,
            min_samples_split=8,
            max_features=0.5,
            random_state=random_state,
            n_jobs=-1,
        )

    return Pipeline([("pre", pre), ("model", estimator)])


def _fit_mapie_model(
    base_model: Pipeline,
    X: pd.DataFrame,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    alpha: float,
    random_state: int,
) -> tuple[Any, np.ndarray, np.ndarray, np.ndarray, np.ndarray, str]:
    if MAPIE_API == "legacy":
        mapie_model = MapieRegressor(
            estimator=base_model,
            method="plus",
            cv=_time_series_cv(len(X_train)),
            n_jobs=-1,
        )
        mapie_model.fit(X_train, y_train)
        test_pred, test_pis = mapie_model.predict(X_test, alpha=alpha)
        all_pred, all_pis = mapie_model.predict(X, alpha=alpha)
        return (
            mapie_model,
            test_pred,
            test_pis,
            all_pred,
            all_pis,
            "MAPIE CV+ (legacy plus)",
        )

    if MAPIE_API == "cross_conformal":
        mapie_model = CrossConformalRegressor(
            estimator=base_model,
            confidence_level=1 - alpha,
            cv=_time_series_cv(len(X_train)),
            n_jobs=-1,
            random_state=random_state,
        )
        mapie_model.fit_conformalize(X_train, y_train)
        test_pred, test_pis = mapie_model.predict_interval(X_test)
        all_pred, all_pis = mapie_model.predict_interval(X)
        return (
            mapie_model,
            test_pred,
            test_pis,
            all_pred,
            all_pis,
            "MAPIE CrossConformal",
        )

    raise ImportError("No supported MAPIE regression API found")


def _prediction_metrics(
    y_test_np: np.ndarray,
    test_pred: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    alpha: float,
) -> dict:
    coverage = float(np.mean((y_test_np >= lower) & (y_test_np <= upper)))
    interval_width_mean = float(np.mean(upper - lower))
    return {
        "mae": float(mean_absolute_error(y_test_np, test_pred)),
        "rmse": float(root_mean_squared_error(y_test_np, test_pred)),
        "r2": float(r2_score(y_test_np, test_pred)),
        "smape": _smape(y_test_np, test_pred),
        "maape": _maape(y_test_np, test_pred),
        "wape": _wape(y_test_np, test_pred),
        "coverage": coverage,
        "interval_width_mean": interval_width_mean,
        "winkler_score": _winkler_score(y_test_np, lower, upper, alpha),
        "crps_pinball": _crps_pinball(y_test_np, lower, upper, alpha),
    }


def _naive_baseline_metrics(
    y_train: pd.Series,
    y_test: pd.Series,
) -> dict:
    """Compute a leakage-safe naive baseline using train mean only."""
    y_test_np = y_test.to_numpy(dtype=float)
    baseline_pred = np.full(len(y_test_np), float(y_train.mean()), dtype=float)
    return {
        "naive_mae": float(mean_absolute_error(y_test_np, baseline_pred)),
        "naive_rmse": float(root_mean_squared_error(y_test_np, baseline_pred)),
        "naive_r2": float(r2_score(y_test_np, baseline_pred)),
    }


def _qhat_from_residuals(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    alpha: float,
) -> float:
    """Compute conformal qhat from held-out residuals."""
    residuals = np.abs(y_true - y_pred)
    return float(np.quantile(residuals, np.clip(1.0 - alpha, 0.0, 1.0)))


def _importance_payload(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    random_state: int,
) -> tuple[list[dict], ColumnTransformer, Any, list[str]]:
    importance_model = _build_model(random_state=random_state)
    importance_model.fit(X_train, y_train)
    estimator = importance_model.named_steps["model"]
    pre = importance_model.named_steps["pre"]
    num_features = list(pre.transformers_[0][2])
    ohe = pre.named_transformers_["cat"]
    cat_features = list(ohe.get_feature_names_out(pre.transformers_[1][2]))
    tfidf_features = list(pre.named_transformers_["tfidf"].get_feature_names_out())
    feature_names = num_features + cat_features + tfidf_features
    importances = getattr(estimator, "feature_importances_", np.array([]))
    if len(importances) != len(feature_names):
        return [], pre, estimator, feature_names
    top_idx = np.argsort(-importances)[:15]
    feat_imp = [
        {"feature": feature_names[i], "importance": float(importances[i])}
        for i in top_idx
    ]
    return feat_imp, pre, estimator, feature_names


def _diagnostics_payload(
    y_test_np: np.ndarray,
    test_pred: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
) -> dict:
    residuals = y_test_np - test_pred
    if len(y_test_np) > 0:
        sample_n = min(180, len(y_test_np))
        sample_idx = np.linspace(0, len(y_test_np) - 1, num=sample_n, dtype=int)
    else:
        sample_idx = np.array([], dtype=int)
    diagnostic_points = [
        {
            "index": int(i),
            "actual": float(y_test_np[i]),
            "predicted": float(test_pred[i]),
            "residual": float(residuals[i]),
            "pi_low": float(lower[i]),
            "pi_high": float(upper[i]),
        }
        for i in sample_idx
    ]
    hist_counts, hist_edges = (
        np.histogram(residuals, bins=20)
        if len(residuals)
        else (np.array([]), np.array([]))
    )
    residual_hist = [
        {
            "bin_left": float(hist_edges[i]),
            "bin_right": float(hist_edges[i + 1]),
            "count": int(hist_counts[i]),
        }
        for i in range(len(hist_counts))
    ]
    return {"points": diagnostic_points, "residual_histogram": residual_hist}


def _build_shap_summary(
    X: pd.DataFrame,
    pre: ColumnTransformer,
    estimator: Any,
    feature_names: list[str],
    random_state: int,
) -> dict:
    shap_summary = {
        "available": False,
        "top_features": [],
        "beeswarm_points": [],
        "feature_order": [],
    }
    try:
        import shap

        shap_sample = X.sample(min(180, len(X)), random_state=random_state)
        Xt_shap = pre.transform(shap_sample)
        Xt_shap_dense = (
            Xt_shap.toarray() if hasattr(Xt_shap, "toarray") else np.asarray(Xt_shap)
        )
        explainer = shap.TreeExplainer(estimator)
        shap_values = explainer.shap_values(Xt_shap_dense)
        shap_arr = np.asarray(shap_values)
        if shap_arr.ndim == 3:
            shap_arr = shap_arr[0]
        mean_abs_shap = np.mean(np.abs(shap_arr), axis=0)
        top_shap_idx = np.argsort(-mean_abs_shap)[:12]
        beeswarm_top_idx = top_shap_idx[:10]

        beeswarm_points: list[dict[str, float | int | str]] = []
        for rank, feature_idx in enumerate(beeswarm_top_idx):
            feature_values = Xt_shap_dense[:, feature_idx]
            fv_min = float(np.min(feature_values)) if len(feature_values) else 0.0
            fv_max = float(np.max(feature_values)) if len(feature_values) else 0.0
            fv_span = fv_max - fv_min
            if fv_span <= 1e-12:
                fv_norm = np.full_like(feature_values, 0.5, dtype=float)
            else:
                fv_norm = (feature_values - fv_min) / fv_span

            rng = np.random.default_rng(seed=random_state + rank)
            jitters = rng.uniform(-0.3, 0.3, size=len(feature_values))

            for row_idx in range(len(feature_values)):
                beeswarm_points.append(
                    {
                        "feature": feature_names[feature_idx],
                        "feature_rank": int(rank),
                        "sample_index": int(row_idx),
                        "shap_value": float(shap_arr[row_idx, feature_idx]),
                        "feature_value": float(feature_values[row_idx]),
                        "feature_value_norm": float(fv_norm[row_idx]),
                        "jitter": float(jitters[row_idx]),
                    }
                )

        shap_summary = {
            "available": True,
            "top_features": [
                {
                    "feature": feature_names[i],
                    "mean_abs_shap": float(mean_abs_shap[i]),
                }
                for i in top_shap_idx
            ],
            "feature_order": [feature_names[i] for i in beeswarm_top_idx],
            "beeswarm_points": beeswarm_points,
        }
    except Exception as e:
        logger.error("SHAP generation error: %s", e, exc_info=True)
    return shap_summary


def _log_mlflow_inference(
    df: pd.DataFrame,
    X: pd.DataFrame,
    test_size: float,
    alpha: float,
    method_name: str,
    metrics: dict,
    feat_imp: list[dict],
    shap_summary: dict,
) -> None:
    if not (MLFLOW_AVAILABLE and MLFLOW_TRACKING_ENABLED):
        return
    try:
        mlflow.set_experiment("content-insights-inference")
        with mlflow.start_run(run_name="predictive_inference", nested=True):
            mlflow.log_param("test_size", test_size)
            mlflow.log_param("alpha", alpha)
            mlflow.log_param("n_samples", len(df))
            mlflow.log_param("n_features", X.shape[1])
            mlflow.log_param("method", method_name)

            for metric_name in (
                "mae",
                "rmse",
                "r2",
                "smape",
                "maape",
                "wape",
                "coverage",
                "interval_width_mean",
                "winkler_score",
                "crps_pinball",
            ):
                mlflow.log_metric(metric_name, metrics[metric_name])
            mlflow.log_metric("median_interval_width", metrics["qhat"] * 2.0)
            mlflow.log_metric(
                "shap_available", 1.0 if shap_summary["available"] else 0.0
            )

            for i, feat in enumerate(feat_imp[:5]):
                mlflow.log_metric(f"importance_rank_{i+1}", feat["importance"])
    except Exception as e:
        logger.warning("MLflow logging warning: %s", e)


def fit_predictive_with_conformal(
    df: pd.DataFrame,
    random_state: int,
    test_size: float,
    alpha: float,
) -> tuple[pd.DataFrame, PredictiveArtifacts]:
    """Fit leakage-safe predictive model with conformal prediction intervals.

    Uses only pre-publication features and a video_id + temporal split.
    This prevents target-component leakage and future-data leakage.

    Args:
        df: Input DataFrame with engagement_rate target
        random_state: Random seed for reproducibility
        test_size: Fraction for test split
        alpha: Miscoverage level (e.g., 0.10 for 90% coverage)

    Returns:
        Tuple of (predictions_df, PredictiveArtifacts)
    """
    if not MAPIE_AVAILABLE:
        raise ImportError(
            "MAPIE is required for conformal prediction intervals. "
            "Install with: pip install mapie"
        )

    y = pd.to_numeric(df["engagement_rate"], errors="coerce").fillna(0.0)
    X = _select_feature_frame(df)
    _assert_no_leakage_features(X)
    dates = pd.to_datetime(df.get("publish_date"), errors="coerce")
    video_ids = df.get("video_id", pd.Series(range(len(df)), index=df.index))

    if dates.isna().all():
        # Fallback for datasets without dates: deterministic train/test, then carve val from train.
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.25, random_state=random_state
        )
    else:
        # Explicit train/val/test using video_id grouping + temporal ordering.
        valid_dates = dates.fillna(dates.min())
        val_size = test_size  # with test_size=0.20, this yields ~60/20/20
        X_train, X_val, X_test, y_train, y_val, y_test = (
            _videoid_temporal_split_train_val_test(
                X=X,
                y=y,
                dates=valid_dates,
                video_ids=video_ids,
                val_size=val_size,
                test_size=test_size,
            )
        )

    logger.info(
        "split sizes train/val/test: %d / %d / %d",
        len(X_train),
        len(X_val),
        len(X_test),
    )

    base_model = _build_model(random_state=random_state)
    mapie_model, test_pred, test_pis, all_pred, all_pis, method_name = _fit_mapie_model(
        base_model=base_model,
        X=X,
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        alpha=alpha,
        random_state=random_state,
    )

    lower, upper = _extract_interval_bounds(test_pis)
    y_test_np = y_test.to_numpy()
    metrics = _prediction_metrics(y_test_np, test_pred, lower, upper, alpha)

    all_low, all_high = _extract_interval_bounds(all_pis)
    y_test_np_for_q = y_test.to_numpy()
    qhat = _qhat_from_residuals(y_test_np_for_q, test_pred, alpha)

    out = df.copy()
    out["engagement_pred"] = all_pred.astype(float)
    out["engagement_pi_low"] = all_low.astype(float)
    out["engagement_pi_high"] = all_high.astype(float)

    feat_imp, pre, estimator, feature_names = _importance_payload(
        X_train, y_train, random_state
    )
    diagnostics = _diagnostics_payload(y_test_np, test_pred, lower, upper)
    shap_summary = _build_shap_summary(X, pre, estimator, feature_names, random_state)

    baseline_metrics = _naive_baseline_metrics(y_train=y_train, y_test=y_test)
    mae_uplift = baseline_metrics["naive_mae"] - metrics["mae"]
    target_coverage = 1.0 - alpha
    coverage_error_abs = abs(metrics["coverage"] - target_coverage)

    metrics.update(
        {
            "qhat": qhat,
            "alpha": alpha,
            "method": method_name,
            "target_coverage": float(target_coverage),
            "coverage_error_abs": float(coverage_error_abs),
            "mae_uplift_vs_naive": float(mae_uplift),
            "model_beats_naive": bool(mae_uplift > 0.0),
            "scientific_acceptance": bool(
                (mae_uplift > 0.0) and (coverage_error_abs <= 0.05)
            ),
            **baseline_metrics,
        }
    )

    artifacts = PredictiveArtifacts(
        model=mapie_model,
        qhat=qhat,
        alpha=alpha,
        metrics=metrics,
        feature_importances=feat_imp,
        diagnostics=diagnostics,
        shap_summary=shap_summary,
    )

    _log_mlflow_inference(
        df=df,
        X=X,
        test_size=test_size,
        alpha=alpha,
        method_name=method_name,
        metrics=metrics,
        feat_imp=feat_imp,
        shap_summary=shap_summary,
    )

    logger.info(
        f"fit_predictive_with_conformal completed: r2={metrics.get('r2', np.nan):.4f}, "
        f"coverage={metrics.get('coverage', np.nan):.3f}"
    )

    return out, artifacts
