from pathlib import Path
import json

from app.etl import load_clean
from app.feature_utils import extract_features
from scripts.train_pipeline import main as train_main


def test_etl_loads_and_has_columns():
    root = Path(__file__).resolve().parents[3]
    data_path = root / 'sample_videos.csv'
    df = load_clean(data_path)
    assert len(df) > 0
    assert 'engagement_rate' in df.columns


def test_feature_extraction_consistent():
    root = Path(__file__).resolve().parents[3]
    df = load_clean(root / 'sample_videos.csv')
    X = extract_features(df)
    assert X.shape[0] == len(df)
    assert set(['views','avg_watch_time_per_view']).issubset(set(X.columns))


def test_quick_training_creates_artifacts(tmp_path):
    # Run a quick training (small trees) — should succeed and write artifacts under models/
    root = Path(__file__).resolve().parents[3]
    # point cwd to project root for script behavior
    prev_cwd = None
    import os
    prev_cwd = os.getcwd()
    os.chdir(root)
    try:
        ok = train_main(n_estimators=5, quick=True)
        assert ok is True
        models_dir = root / 'models'
        manifest = json.loads((models_dir / 'manifest.json').read_text())
        assert 'predictive_base' in manifest
    finally:
        os.chdir(prev_cwd)
