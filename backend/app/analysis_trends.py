"""Time series trend analysis and correlation discovery.

This module implements temporal pattern detection:
1. weekly_trend_views(): Linear regression on weekly aggregates (OLS)
   - TheilSenRegressor: Robust to outliers (better than OLS)
   - Returns slope (trend direction) + intercept (baseline)

2. spearman_engagement_vs_views(): Rank correlation between metrics
   - Spearman vs Pearson: Better for non-linear relationships
   - P-value indicates statistical significance

3. correlations(): Pairwise Pearson correlations across features
   - Identifies multicollinearity (features too correlated)
   - Detection: High correlations (>0.9) indicate redundant features

CURRENT CAPABILITIES (LIMITED):
- Daily/weekly aggregation only
- No month-of-year seasonality analysis
- No day-of-week effects
- No autocorrelation detection (ACF/PACF)
- No seasonal decomposition

CHALLENGES & DESIGN DECISIONS:
1. Basic trend only (slope): Misses cyclical patterns
   - Nature: Linear assumption may not hold for video platforms
   - Reality: Engagement follows weekly + monthly cycles

2. No holiday effect detection:
   - 2023-2024 data covers 2 Christmases, 2 New Years
   - But not enough cycles for robust holiday patterns

3. Spearman → non-linearity safe, but correlation doesn't imply causation
   - Views causes engagement? Or viral content gets both?

4. Weekly aggregation loses intra-week patterns:
   - Treats Monday-Sunday as single unit
   - May want day-of-week analysis (Monday vs Friday effects)

DATA AVAILABILITY:
- Span: 2023-01-01 to 2024-12-29 (728 days = 1.99 years)
- Videos: ~1.37 per day average
- Coverage: Perfect for day-of-week analysis, marginal for seasonal cycles

FUTURE ENHANCEMENTS:
1. Day-of-Week Analysis (RECOMMENDED):
   Example:
   ```python
   def seasonality_by_dow(df):
       df['dow'] = df['publish_date'].dt.day_name()
       dow_stats = df.groupby('dow')['engagement_rate'].agg(['mean', 'std', 'count'])
       best_day = dow_stats['mean'].idxmax()  # e.g., 'Tuesday'
       return dow_stats.sort_values('mean', ascending=False)
       # Result: Tuesday videos get 28% more engagement than Friday
   ```

2. STL Decomposition (NOW POSSIBLE): 2 years of data available
   Example:
   ```python
   from statsmodels.tsa.seasonal import STL

   weekly_views = df.groupby('publish_week')['views'].mean()
   stl = STL(weekly_views, seasonal=52, trend=25)
   result = stl.fit()

   trend = result.trend              # Long-term growth
   seasonal = result.seasonal        # Repeating 52-week cycle
   residual = result.resid           # Anomalies
   seasonal_strength = 1 - var(residual) / var(seasonal + residual)
   # Indicates: 35% of variation is seasonal (strong signal!)
   ```

3. GenAI Content Recommendation:
   Example:
   ```python
   # Use GPT to explain seasonality patterns to creators
   prompt = f'''Based on these engagement trends:
   - Tuesday videos: +15% engagement
   - December videos: -8% engagement
   - Morning publishes (6-9 AM): +12%

   Provide 3 recommendations for creators.'''

   insights = openai.ChatCompletion.create(
       model="gpt-3.5-turbo",
       messages=[{"role": "user", "content": prompt}]
   )
   # Output: "Publish on Tuesday mornings to maximize engagement..."
   ```

4. Autocorrelation Detection:
   Example:
   ```python
   from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

   weekly_agg = df.groupby('publish_week')['engagement_rate'].mean()
   acf_values = plot_acf(weekly_agg, lags=26)  # 6 months
   # Detects: Are week-52 videos similar to week-0? (annual cycle?)
   ```

5. ARIMA Forecasting:
   Example:
   ```python
   from statsmodels.tsa.arima.model import ARIMA

   weekly_agg = df.groupby('publish_week')['views'].mean()
   model = ARIMA(weekly_agg, order=(1,1,1))
   results = model.fit()
   forecast = results.get_forecast(steps=4)  # Forecast 4 weeks
   # Predict next month's engagement trends
   ```
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import TheilSenRegressor

logger = logging.getLogger(__name__)


def _spectral_entropy_metrics(x: np.ndarray) -> dict:
    from scipy.signal import periodogram

    _, psd = periodogram(x)
    psd_norm = psd / (psd.sum() + 1e-12)
    psd_norm = psd_norm[psd_norm > 0]
    spec_entropy = float(-np.sum(psd_norm * np.log2(psd_norm)) / np.log2(len(psd_norm)))
    return {
        "spectral_entropy": round(spec_entropy, 6),
        "foreca_score": round(1.0 - spec_entropy, 6),
    }


def _permutation_entropy_metric(x: np.ndarray, n: int) -> dict:
    import math

    m, tau = 3, 1
    patterns: dict = {}
    for i in range(n - (m - 1) * tau):
        motif = tuple(np.argsort(x[i : i + m * tau : tau]))  # noqa: E203
        patterns[motif] = patterns.get(motif, 0) + 1
    total = sum(patterns.values())
    probs = np.array([v / total for v in patterns.values()])
    max_entropy = math.log2(math.factorial(m))
    perm_entropy = float(-np.sum(probs * np.log2(probs + 1e-12)) / max_entropy)
    return {"permutation_entropy": round(perm_entropy, 6)}


def _hurst_metrics(x: np.ndarray, n: int) -> dict:
    lag_values = [max(2, n // 8), max(4, n // 4), max(8, n // 2)]
    lag_values = sorted(set(lag for lag in lag_values if lag < n))
    rs_vals = []
    for lag in lag_values:
        sub = x[:lag]
        mean_sub = sub.mean()
        deviate = np.cumsum(sub - mean_sub)
        r = deviate.max() - deviate.min()
        s = sub.std(ddof=1) + 1e-12
        rs_vals.append(np.log(r / s))
    log_lags = np.log(lag_values)
    hurst = float(np.polyfit(log_lags, rs_vals, 1)[0])
    if hurst > 0.55:
        interpretation = "trending (persistent)"
    elif hurst < 0.45:
        interpretation = "mean-reverting (anti-persistent)"
    else:
        interpretation = "random walk"
    return {
        "hurst_exponent": round(hurst, 6),
        "hurst_interpretation": interpretation,
    }


def _variance_ratio_metrics(x: np.ndarray, n: int) -> dict:
    k = min(5, n // 4)
    if k < 2:
        return {"variance_ratio": None, "variance_ratio_k": None}
    var1 = float(np.var(np.diff(x), ddof=1))
    vark = float(np.var(x[k:] - x[:-k], ddof=1) / k)
    vr = vark / (var1 + 1e-12)
    return {"variance_ratio": round(vr, 6), "variance_ratio_k": k}


def forecastability_metrics(series: np.ndarray) -> dict:
    """Compute forecastability diagnostics for a univariate time series.

    Metrics align with 'Mastering Modern Time Series Forecasting with Python'
    (Valery):
      - Spectral entropy (normalized): low -> more forecastable, high -> noisy
      - Permutation entropy (normalized): measures ordinal complexity
      - Hurst exponent (R/S): >0.5 trending, 0.5 random, <0.5 mean-reverting
      - Variance ratio VR(k=5): near 1 -> random walk, >1 -> trending
      - ForeCA score proxy (1 - normalized spectral entropy): higher is better
    """
    x = np.asarray(series, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    result: dict = {"n_observations": n}

    for helper in (
        _spectral_entropy_metrics,
        lambda values: _permutation_entropy_metric(values, n),
        lambda values: _hurst_metrics(values, n),
        lambda values: _variance_ratio_metrics(values, n),
    ):
        try:
            result.update(helper(x))
        except Exception:
            logger.debug("Forecastability helper %s failed", helper, exc_info=True)
            if helper is _spectral_entropy_metrics:
                result.update({"spectral_entropy": None, "foreca_score": None})
            elif helper.__name__ == "<lambda>":
                pass

    result.setdefault("permutation_entropy", None)
    result.setdefault("hurst_exponent", None)
    result.setdefault("hurst_interpretation", None)
    result.setdefault("variance_ratio", None)
    result.setdefault("variance_ratio_k", None)
    return result


def correlations(df: pd.DataFrame) -> dict:
    cols = [
        "views",
        "engagement_rate",
        "avg_watch_time_per_view",
        "share_rate",
        "like_rate",
    ]
    return df[cols].corr().round(4).to_dict()


def spearman_engagement_vs_views(df: pd.DataFrame) -> dict:
    rho, p = stats.spearmanr(df["engagement_rate"], df["views"])
    return {"rho": float(rho), "p_value": float(p)}


def weekly_trend_views(df: pd.DataFrame) -> dict:
    weekly = (
        df.groupby("publish_week")["views"]
        .mean()
        .reset_index()
        .sort_values("publish_week")
    )
    if len(weekly) < 4:
        return {"note": "not enough weeks for trend", "weeks": int(len(weekly))}
    X = np.arange(len(weekly)).reshape(-1, 1)
    y = weekly["views"].astype(float).to_numpy()
    model = TheilSenRegressor(random_state=42)
    model.fit(X, y)
    return {
        "weeks": int(len(weekly)),
        "slope": float(model.coef_[0]),
        "intercept": float(model.intercept_),
        "series": weekly.to_dict(orient="records"),
    }
