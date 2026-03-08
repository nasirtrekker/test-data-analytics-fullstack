"""Lightweight training script used by CI and tests.
Saves versioned artifacts into `models/` using backend.app.model_versioning.
"""
from pathlib import Path
import joblib
import json
import numpy as np

from backend.app.model_versioning import save_model_versioned
from backend.app.feature_utils import extract_features, feature_columns
from backend.app.etl import load_clean
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans


def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    last_match = None
    # walk up to filesystem root, remember the highest directory containing sample_videos.csv
    while True:
        if (p / 'sample_videos.csv').exists():
            last_match = p
        if p.parent == p:
            break
        p = p.parent
    if last_match:
        return last_match
    return start.resolve().parents[1]


def main(n_estimators: int = 10, quick: bool = True):
    ROOT = find_repo_root(Path(__file__).resolve())
    data_path = ROOT / 'sample_videos.csv'
    models_dir = ROOT / 'models'
    df = load_clean(data_path)
    X = extract_features(df)
    y = df['engagement_rate'].fillna(0)

    # train a small RF for quick CI runs
    rf = RandomForestRegressor(n_estimators=n_estimators, random_state=42)
    rf.fit(X, y)
    # save versioned base model
    save_model_versioned({'model': rf, 'feature_cols': feature_columns()}, 'predictive_base', models_dir)

    # simple clustering artifact
    k = 3 if len(df) > 10 else 1
    if k > 1:
        km = KMeans(n_clusters=k, random_state=42).fit(X.values)
        save_model_versioned({'kmeans': km}, 'clusters', models_dir)

    # model_versioning.save_model_versioned updated the manifest.json; nothing else to do
    return True


if __name__ == '__main__':
    main()
