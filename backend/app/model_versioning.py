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
