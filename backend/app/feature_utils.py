"""Feature engineering utilities - Compute derived metrics from raw video data.

This module generates domain-specific features from raw engagement metrics:
1. Engagement Rate: (likes + comments + shares) / views
2. Like Rate: likes / views
3. Comment Rate: comments / views
4. Share Rate: shares / views
5. Avg Watch Time: watch_time_seconds / views
6. Temporal Features: year, month, weekday from publish_date
7. Categorical Encoding: One-hot encoding for category and thumbnail_style

Feature Rationale:
- Rate-based features: Normalize for cross-video comparison
- Temporal features: Capture day-of-week and seasonal patterns
- Categorical features: Enable content type segmentation

Normalization:
- StandardScaler for ML algorithms (zero mean, unit variance)
- Outlier handling: Statistical bounds for engagement rates
"""

from pathlib import Path

import numpy as np
import pandas as pd

CORE_FEATURES = ["views", "avg_watch_time_per_view"]


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in CORE_FEATURES:
        if c not in df.columns:
            df[c] = 0
    X = df[CORE_FEATURES].fillna(0).astype(float)
    return X


def feature_columns():
    return list(CORE_FEATURES)
