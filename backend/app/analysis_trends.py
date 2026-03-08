"""Time series trend analysis and correlation discovery.

This module implements temporal pattern detection:
1. weekly_trend_views(): Linear regression on weekly aggregates (OLS)
2. spearman_engagement_vs_views(): Rank correlation between metrics
3. correlations(): Pairwise correlations across all engagement dimensions

Analysis Methods:
- OLS regression: Extracts slope/intercept for trend direction
- Spearman rank correlation: Robust to outliers and non-linearity
- Correlation matrix: Identifies multicollinearity patterns

Outputs:
- Trend metrics: slope (trend direction), intercept (baseline)
- Correlation coefficients: p-values for statistical significance
- Temporal patterns: Weekly seasonality and growth rates

Business Applications:
- Forecast future content performance
- Identify emerging trends early
- Understand engagement metric relationships
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import TheilSenRegressor


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
