"""Clustering analysis - Segment videos by engagement patterns using K-Means and DBSCAN.

This module implements dual-clustering approach:
1. K-Means: Partitions data into k=2 clusters (viral vs. engagement-focused)
2. DBSCAN: Density-based outlier detection (eps=0.8, min_samples=8)

Features (StandardScaler normalized):
- views: Raw reach metric
- engagement_rate: (likes + comments + shares) / views
- avg_watch_time_per_view: Retention indicator
- share_rate: Virality signal

Output:
- cluster: K-Means label (0 or 1)
- dbscan_cluster: DBSCAN label (-1 for noise/anomalies)

Business segmentation:
- Cluster 0: High-reach content (>1M views)
- Cluster 1: High-engagement content (>5% engagement)
- Noise (-1): Anomalous performance patterns
"""

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
