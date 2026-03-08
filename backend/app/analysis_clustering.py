from __future__ import annotations

import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler


def add_clusters(df: pd.DataFrame, k: int, random_state: int) -> pd.DataFrame:
    feats = df[
        ["views", "engagement_rate", "avg_watch_time_per_view", "share_rate"]
    ].copy()
    X = StandardScaler().fit_transform(feats)
    km = KMeans(n_clusters=k, n_init="auto", random_state=random_state)
    db = DBSCAN(eps=0.8, min_samples=8)
    out = df.copy()
    out["cluster"] = km.fit_predict(X)
    # DBSCAN label -1 means noise/outlier points in density-based clustering.
    out["dbscan_cluster"] = db.fit_predict(X)
    return out
