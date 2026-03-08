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
