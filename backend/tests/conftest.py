import sys
from pathlib import Path


# Ensure `import app` resolves to backend/app during test collection.
backend_dir = Path(__file__).resolve().parents[1]
backend_dir_str = str(backend_dir)
if backend_dir_str not in sys.path:
    sys.path.insert(0, backend_dir_str)
