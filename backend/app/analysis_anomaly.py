from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest


def add_anomalies(
    df: pd.DataFrame, contamination: float, random_state: int
) -> pd.DataFrame:
    X = df[["views", "engagement_rate", "avg_watch_time_per_view"]].copy()
    iso = IsolationForest(contamination=contamination, random_state=random_state)
    out = df.copy()
    out["is_anomaly"] = iso.fit_predict(X) == -1
    return out
