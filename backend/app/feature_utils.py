"""Feature engineering utilities - Compute derived metrics from raw video data.

This module generates domain-specific features from raw engagement metrics:
1. Engagement Rate: (likes + comments + shares) / views
2. Like Rate: likes / views
3. Comment Rate: comments / views
4. Share Rate: shares / views
5. Avg Watch Time: watch_time_seconds / views
6. Temporal Features: year, month, weekday from publish_date (cyclical encoding)
7. Categorical Encoding: One-hot encoding for category and thumbnail_style

Feature Rationale:
- Rate-based features: Normalize for cross-video comparison
- Temporal features: Capture day-of-week and seasonal patterns
- Categorical features: Enable content type segmentation

Safe Feature Policy:
- extract_features() mirrors the exact feature set used during training
  in analysis_predictive._select_feature_frame() to prevent train/serve skew.
- Only pre-publication features are included (no engagement-derived fields).
"""

import numpy as np
import pandas as pd

# Must stay in sync with analysis_predictive.SAFE_NUMERIC_FEATURES / EARLY_FEATURES
SAFE_NUMERIC_FEATURES = [
    "title_length",
    "avg_word_length",
    "title_upper_ratio",
    "publish_year",
    "month_sin",
    "month_cos",
    "dow_sin",
    "dow_cos",
]
SAFE_CATEGORICAL_FEATURES = ["category", "thumbnail_style"]
TEXT_FEATURE = "title_raw"  # must match analysis_predictive.TEXT_FEATURE


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the same safe feature frame used for predictive model training.

    This mirrors analysis_predictive._select_feature_frame() so that any
    inference outside the full pipeline uses an identical schema.
    """
    out = pd.DataFrame(index=df.index)

    dates = pd.to_datetime(
        df.get("publish_date", pd.Series(dtype=str)), errors="coerce"
    )
    publish_month = dates.dt.month.fillna(1).astype(float)
    publish_weekday = dates.dt.weekday.fillna(0).astype(float)

    titles = df.get("title", pd.Series("", index=df.index)).astype(str).fillna("")
    title_length = titles.str.len().astype(float)
    title_words = titles.str.split().str.len().fillna(1).clip(lower=1).astype(float)

    derivations: dict = {
        "title_length": title_length,
        "avg_word_length": title_length / title_words,
        "title_upper_ratio": titles.str.count(r"[A-Z]") / title_length.clip(lower=1),
        "publish_year": dates.dt.year.fillna(2023).astype(float),
        "month_sin": np.sin(2 * np.pi * publish_month / 12),
        "month_cos": np.cos(2 * np.pi * publish_month / 12),
        "dow_sin": np.sin(2 * np.pi * publish_weekday / 7),
        "dow_cos": np.cos(2 * np.pi * publish_weekday / 7),
    }

    for col in SAFE_NUMERIC_FEATURES:
        if col in derivations:
            out[col] = derivations[col].fillna(0.0)
        elif col in df.columns:
            out[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        else:
            out[col] = 0.0
    for col in SAFE_CATEGORICAL_FEATURES:
        if col in df.columns:
            out[col] = df[col].astype(str).fillna("unknown")
        else:
            out[col] = "unknown"
    out[TEXT_FEATURE] = titles.values
    return out


def feature_columns():
    return (
        list(SAFE_NUMERIC_FEATURES) + list(SAFE_CATEGORICAL_FEATURES) + [TEXT_FEATURE]
    )
