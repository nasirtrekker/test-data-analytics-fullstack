"""Anomaly detection - Ensemble of Isolation Forest + Local Outlier Factor.

Uses 6 engagement features for richer signal. Each method votes independently;
the union is flagged as `is_anomaly`, and the consensus (both agree) is stored
in `anomaly_consensus` for high-confidence outlier analysis.
"""

from __future__ import annotations

import logging

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

ANOMALY_FEATURES = [
    "views",
    "engagement_rate",
    "avg_watch_time_per_view",
    "like_rate",
    "comment_rate",
    "share_rate",
]


def add_anomalies(
    df: pd.DataFrame, contamination: float, random_state: int
) -> pd.DataFrame:
    available = [f for f in ANOMALY_FEATURES if f in df.columns]
    X = StandardScaler().fit_transform(df[available].fillna(0.0))

    iso = IsolationForest(
        contamination=contamination, random_state=random_state, n_jobs=-1
    )
    iso_labels = iso.fit_predict(X) == -1

    lof = LocalOutlierFactor(
        n_neighbors=min(20, max(5, len(df) // 50)),
        contamination=contamination,
    )
    lof_labels = lof.fit_predict(X) == -1

    out = df.copy()
    out["is_anomaly"] = iso_labels | lof_labels  # union — high recall
    out["anomaly_consensus"] = iso_labels & lof_labels  # consensus — high precision

    n_union = int(out["is_anomaly"].sum())
    n_consensus = int(out["anomaly_consensus"].sum())
    logger.info(
        "Anomalies: %d union (%d IF + %d LOF), %d consensus",
        n_union,
        int(iso_labels.sum()),
        int(lof_labels.sum()),
        n_consensus,
    )
    return out
