from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", extra="ignore")

    # Environment
    environment: str = "development"  # development, production, testing
    debug: bool = True
    log_level: str = "INFO"

    # Data configuration
    data_path: str = "../sample_videos.csv"
    random_state: int = 42

    # Analytics configuration
    # Clustering default aligns with notebook optimization: k=2 by silhouette.
    # If business needs finer segmentation, raise APP_CLUSTER_K (for example 4).
    cluster_k: int = 2
    anomaly_contamination: float = 0.05

    # Predictive + conformal
    test_size: float = 0.2
    alpha: float = 0.1  # 90% intervals

    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    api_reload: bool = True

    # CORS configuration (production should restrict this)
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"


settings = Settings()
