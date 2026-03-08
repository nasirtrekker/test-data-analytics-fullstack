from __future__ import annotations

"""Application configuration - Environment-aware settings management.

This module centralizes configuration parameters with environment variable overrides:
1. Data Source: CSV file path (default: sample_videos.csv)
2. ML Hyperparameters: cluster_k, contamination, random_state
3. Train/Test Split: test_size for model validation
4. Conformal Prediction: alpha for coverage level
5. MLflow Tracking: URI and run ID management
6. CORS Origins: Localhost for development

Configuration Hierarchy:
1. Environment variables (highest priority)
2. .env file (default: .env.development)
3. Hardcoded defaults (fallback)

Supported Environments:
- development: Local testing with verbose logging
- production: Kubernetes/Docker deployment with MLflow PostgreSQL backend

Settings Validation:
- Pydantic schema enforcement
- Type coercion (strings -> int/bool)
- Required field checks
"""

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
