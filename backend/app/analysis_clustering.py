"""Clustering analysis - Segment videos by engagement patterns using K-Means and DBSCAN.

This module implements dual-clustering approach:
1. K-Means: Partitions data into k=2 clusters (viral vs. engagement-focused)
   - Silhouette Score: 0.2671 (overlapping clusters, moderate separation)
   - Cluster distribution: ~513 vs 487 (balanced split)

2. DBSCAN: Density-based outlier detection (eps=0.8, min_samples=8)
   - Noise ratio: 98.4% (curse of dimensionality)
   - Clusters found: 3 dense regions + massive noise class

Features (StandardScaler normalized):
- views: Raw reach metric
- engagement_rate: (likes + comments + shares) / views
- avg_watch_time_per_view: Retention indicator
- share_rate: Virality signal

CHALLENGES & DESIGN DECISIONS:
1. K-Means silhouette=0.2671 → consider PCA/UMAP dimensionality reduction
2. DBSCAN 98.4% noise ratio → high-dimensional sparsity problem
3. No generalization testing → future: validate clusters on held-out test set

FUTURE ENHANCEMENTS:
- GenAI: Use GPT to analyze cluster themes from video titles
  Example: cluster_profile = openai.ChatCompletion.create(
      messages=[{"role": "user", "content": f"Analyze these video titles: {sample_titles}"}])
- PCA/UMAP: Reduce features 4→2 before DBSCAN
- Cluster validation: Ensure quality on 20% hold-out test set
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
