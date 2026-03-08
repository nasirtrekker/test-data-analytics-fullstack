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
