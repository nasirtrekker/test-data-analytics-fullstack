from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

from .analysis_anomaly import add_anomalies
from .analysis_clustering import add_clusters
from .analysis_embeddings import build_embeddings, similar_titles
from .analysis_predictive import PredictiveArtifacts, fit_predictive_with_conformal
from .analysis_trends import (
    correlations,
    spearman_engagement_vs_views,
    weekly_trend_views,
)
from .etl import load_clean


@dataclass(frozen=True)
class State:
    df: pd.DataFrame
    tfidf_mat: Any
    predictive: PredictiveArtifacts


def build_state(
    data_path: str,
    cluster_k: int,
    contamination: float,
    random_state: int,
    test_size: float,
    alpha: float,
) -> State:
    df = load_clean(data_path)
    df = add_clusters(df, k=cluster_k, random_state=random_state)
    df = add_anomalies(df, contamination=contamination, random_state=random_state)
    df, pred_art = fit_predictive_with_conformal(
        df=df, random_state=random_state, test_size=test_size, alpha=alpha
    )
    _, mat = build_embeddings(df["title"].astype(str).tolist())
    return State(df=df, tfidf_mat=mat, predictive=pred_art)


def overview_metrics(df: pd.DataFrame) -> dict:
    dbscan_non_noise = df[df["dbscan_cluster"] != -1]["dbscan_cluster"].nunique()
    dbscan_noise = int((df["dbscan_cluster"] == -1).sum())
    return {
        "rows": int(len(df)),
        "total_views": int(df["views"].sum()),
        "avg_engagement_rate": float(df["engagement_rate"].mean()),
        "avg_watch_time_per_view": float(df["avg_watch_time_per_view"].mean()),
        "cluster_count": int(df["cluster"].nunique()),
        "dbscan_cluster_count": int(dbscan_non_noise),
        "dbscan_noise_count": dbscan_noise,
        "anomaly_count": int(df["is_anomaly"].sum()),
    }


def insights(df: pd.DataFrame, predictive: PredictiveArtifacts) -> dict:
    clustering_features = [
        "views",
        "engagement_rate",
        "avg_watch_time_per_view",
        "share_rate",
    ]
    X = StandardScaler().fit_transform(df[clustering_features].to_numpy())
    kmeans_labels = df["cluster"].to_numpy()
    dbscan_labels = df["dbscan_cluster"].to_numpy()

    kmeans_sil = (
        float(silhouette_score(X, kmeans_labels))
        if len(np.unique(kmeans_labels)) > 1
        else None
    )
    kmeans_dbi = (
        float(davies_bouldin_score(X, kmeans_labels))
        if len(np.unique(kmeans_labels)) > 1
        else None
    )
    kmeans_chs = (
        float(calinski_harabasz_score(X, kmeans_labels))
        if len(np.unique(kmeans_labels)) > 1
        else None
    )

    dbscan_mask = dbscan_labels != -1
    dbscan_unique = (
        np.unique(dbscan_labels[dbscan_mask]) if np.any(dbscan_mask) else np.array([])
    )
    dbscan_sil = (
        float(silhouette_score(X[dbscan_mask], dbscan_labels[dbscan_mask]))
        if len(dbscan_unique) > 1
        else None
    )

    return {
        "correlations": correlations(df),
        "spearman_engagement_vs_views": spearman_engagement_vs_views(df),
        "weekly_trend_views": weekly_trend_views(df),
        "clustering_diagnostics": {
            "kmeans": {
                "silhouette": kmeans_sil,
                "davies_bouldin": kmeans_dbi,
                "calinski_harabasz": kmeans_chs,
            },
            "dbscan": {
                "silhouette_non_noise": dbscan_sil,
                "noise_count": int((dbscan_labels == -1).sum()),
                "noise_ratio": float((dbscan_labels == -1).mean()),
                "cluster_count_non_noise": int(len(dbscan_unique)),
            },
        },
        "cluster_summary": (
            df.groupby("cluster")[
                ["views", "engagement_rate", "avg_watch_time_per_view"]
            ]
            .mean()
            .round(4)
            .reset_index()
            .to_dict(orient="records")
        ),
        "dbscan_summary": (
            df.groupby("dbscan_cluster")["video_id"]
            .count()
            .rename("count")
            .reset_index()
            .to_dict(orient="records")
        ),
        "anomaly_examples": (
            df[df["is_anomaly"]]
            .sort_values("views", ascending=False)
            .head(10)[["video_id", "title", "views", "engagement_rate"]]
            .to_dict(orient="records")
        ),
        "predictive_model": {
            "metrics": predictive.metrics,
            "top_feature_importances": predictive.feature_importances,
            "diagnostics": predictive.diagnostics,
            "shap_summary": predictive.shap_summary,
        },
    }


def get_similar(df: pd.DataFrame, mat: Any, video_id: str, top_k: int) -> list[dict]:
    return similar_titles(df, mat, video_id=video_id, top_k=top_k)
