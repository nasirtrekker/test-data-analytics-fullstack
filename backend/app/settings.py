from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", extra="ignore")

    data_path: str = "../sample_videos.csv"
    random_state: int = 42
    # Clustering default aligns with notebook optimization: k=2 by silhouette.
    # If business needs finer segmentation, raise APP_CLUSTER_K (for example 4).
    cluster_k: int = 2
    anomaly_contamination: float = 0.05

    # Predictive + conformal
    test_size: float = 0.2
    alpha: float = 0.1  # 90% intervals


settings = Settings()
