"""Anomaly detection - Identify performance outliers using Isolation Forest.

This module implements unsupervised outlier detection:
1. Isolation Forest: Tree-based anomaly scoring algorithm
2. Contamination rate: 0.1 (10% expected anomalies)
3. Feature selection: views, engagement_rate, avg_watch_time_per_view

Algorithm:
- Isolation Forest: Recursively isolates anomalous observations
- Anomaly score: Distance from root in isolation trees
- Binary classification: Normal (0) vs. Anomalous (1)

Anomaly Types:
- Positive anomalies: Unexpectedly viral content (high reach, low production investment)
- Negative anomalies: Underperforming content (expected engagement not achieved)
- Noise: Natural variation in content performance

Business Actions:
- Monitor anomalies in real-time dashboards
- Investigate positive anomalies for replication
- Understand negative anomalies for quality improvements
"""

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
