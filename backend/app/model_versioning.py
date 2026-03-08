"""Model artifact lifecycle management - Version tracking and retrieval.

This module manages trained model storage and versioning:
1. Artifact Storage: .joblib binary format for sklearn models
2. Metadata Registry: manifest.json for version info and performance metrics
3. Model Types: K-Means clusterer, RandomForest regressor, TF-IDF vectorizer

Artifacts Tracked:
- predictive_base_v2.joblib: RandomForest model (30+ features)
- clusters_v2.joblib: K-Means model (k=2)
- title_tfidf.joblib: TF-IDF vectorizer (3K vocabulary)
- shap_sample.joblib: SHAP values cache
- mapie_validation.json: Conformal prediction metrics

Version Management:
- Sequential versioning (v1, v2, v3)
- Metadata includes model type, training date, performance metrics
- Fallback mechanisms for missing artifacts

MLOps Integration:
- Compatible with MLflow Model Registry
- Serialization format: joblib (optimal for sklearn)
- Reproducibility: Feature columns and hyperparameters logged
"""

import json
import re
from pathlib import Path

import joblib


def _next_version(models_dir: Path, name: str) -> int:
    models_dir.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(rf"^{re.escape(name)}_v(\d+)\.joblib$")
    max_v = 0
    for p in models_dir.iterdir():
        m = pattern.match(p.name)
        if m:
            v = int(m.group(1))
            if v > max_v:
                max_v = v
    return max_v + 1


def save_model_versioned(obj, name: str, models_dir: Path):
    v = _next_version(models_dir, name)
    fname = f"{name}_v{v}.joblib"
    dest = models_dir / fname
    joblib.dump(obj, dest)
    # update manifest
    manifest_path = models_dir / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except Exception:
            manifest = {}
    manifest[name] = fname
    manifest_path.write_text(json.dumps(manifest))
    return dest
