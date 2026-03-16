"""Clustering analysis - Segment videos using PCA-reduced K-Means and HDBSCAN.

Approach:
1. PCA to 2 components on scaled 4-feature space → eliminates curse-of-dimensionality.
2. K-Means with silhouette-scan (k=2..8) → picks k with best silhouette score.
3. HDBSCAN replaces DBSCAN → adaptive density, far fewer noise points.

Features (StandardScaler normalized, then PCA-reduced):
- views, engagement_rate, avg_watch_time_per_view, share_rate
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

try:
    from hdbscan import HDBSCAN

    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False
    logger.info("hdbscan not installed — falling back to sklearn HDBSCAN.")
    try:
        from sklearn.cluster import HDBSCAN  # type: ignore[attr-defined]

        HDBSCAN_AVAILABLE = True
    except ImportError:
        logger.warning("No HDBSCAN available — density clustering disabled.")

CLUSTER_FEATURES = ["views", "engagement_rate", "avg_watch_time_per_view", "share_rate"]


def _silhouette_scan(
    X: np.ndarray, k_range: range, random_state: int
) -> tuple[int, dict[int, float]]:
    """Return best k and per-k silhouette scores."""
    scores: dict[int, float] = {}
    for k in k_range:
        labels = KMeans(
            n_clusters=k, n_init="auto", random_state=random_state
        ).fit_predict(X)
        scores[k] = float(silhouette_score(X, labels))
    best_k = max(scores, key=scores.get)  # type: ignore[arg-type]
    return best_k, scores


def add_clusters(df: pd.DataFrame, k: int, random_state: int) -> pd.DataFrame:
    feats = df[CLUSTER_FEATURES].copy()
    scaled = StandardScaler().fit_transform(feats)

    # PCA to 2 dims — enables better separation for both K-Means and HDBSCAN
    pca = PCA(n_components=2, random_state=random_state)
    X_pca = pca.fit_transform(scaled)
    logger.info(
        "PCA variance explained: %.1f%% + %.1f%%",
        pca.explained_variance_ratio_[0] * 100,
        pca.explained_variance_ratio_[1] * 100,
    )

    # Silhouette scan to find optimal k (override caller if scan is better)
    k_range = range(2, min(9, len(df) // 10 + 1))
    if len(k_range) >= 2:
        best_k, sil_scores = _silhouette_scan(X_pca, k_range, random_state)
        logger.info(
            "Silhouette scan: %s → best k=%d (sil=%.4f)",
            sil_scores,
            best_k,
            sil_scores[best_k],
        )
        k = best_k

    km = KMeans(n_clusters=k, n_init="auto", random_state=random_state)
    out = df.copy()
    out["cluster"] = km.fit_predict(X_pca)

    # HDBSCAN on PCA-reduced space
    if HDBSCAN_AVAILABLE:
        hdb = HDBSCAN(min_cluster_size=max(5, len(df) // 50), min_samples=3)
        out["dbscan_cluster"] = hdb.fit_predict(X_pca)
        noise_ratio = float((out["dbscan_cluster"] == -1).mean())
        logger.info("HDBSCAN noise ratio: %.1f%%", noise_ratio * 100)
    else:
        out["dbscan_cluster"] = -1

    return out
