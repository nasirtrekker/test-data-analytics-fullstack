# Demo Guide: Content Insights Platform

Complete guide to run live demos of the content performance analytics platform with MLflow experiment tracking.

---

## Quick Start

### Docker Demo (Fastest - 1 minute)
```bash
cd <repo-root>
./docker-demo.sh up
```

Then open:
- **Frontend**: http://localhost:5173
- **Backend Docs**: http://localhost:8000/docs
- **MLflow UI**: http://localhost:5000

**Stop:**
```bash
./docker-demo.sh down
```

---

### Local Demo with Tmux (5 minutes, best for debugging)
```bash
cd <repo-root>
chmod +x demo.sh
./demo.sh
```

Then open same 3 browser tabs (see Docker demo above).

**To view tmux panes:**
- Already attached and visible on screen
- Navigate panes: `Ctrl+B` then arrow keys
- Detach: `Ctrl+B` then `D`
- Reattach: `tmux attach -t content-insights-demo`

**Kill session:**
```bash
tmux kill-session -t content-insights-demo
```

---

## Demo Modes Comparison

| Feature | Docker | Tmux (Local) |
|---------|--------|------------|
| Setup Speed | 60 sec | 30 sec |
| Setup Complexity | 1 command | 1 command |
| Logs Visibility | Good | Excellent (4 panes) |
| Debugging | Medium | Excellent |
| Backend Reload | No | Yes (auto-reload) |
| Frontend Reload | No | Yes (HMR) |
| Memory Usage | Medium | Light |
| Production-like | Yes | No |

---

## What Each Service Shows

### 1. Frontend Dashboard (http://localhost:5173)
**React dashboard showing:**
- Total views, engagement metrics
- Cluster visualization (2 distinct groups)
- Anomalies table (~100 outliers)
- Predictive panel with R² score (0.99+)
- Similar content recommendations

**Talk points:**
- "Real-time analytics from 1,000 YouTube videos"
- "ML models automatically detect patterns"
- "Predictions with confidence intervals via MAPIE"

---

### 2. Backend API (http://localhost:8000/docs)
**FastAPI documentation showing endpoints:**

```
GET  /health       → Service health check
GET  /metrics      → KPI aggregates (views, engagement)
GET  /filters      → Available categories, dates
GET  /videos       → Video listings with predictions
GET  /insights     → ML model diagnostics
GET  /similar      → Content recommendations
```

**Talk points:**
- "API loads data, trains models on startup"
- "Models cached in memory (thread-safe)"
- "Serialized responses for frontend consumption"

**Quick test:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics | jq
```

---

### 3. MLflow UI (http://localhost:5000)
**Experiment tracking:**

1. Click **Experiments** (left sidebar)
2. Select **`content-insights-training`**
3. View 5+ training runs with:
   - **Parameters**: n_estimators, data_samples, random_state
   - **Metrics**: train_mse, train_r2, kmeans_inertia
   - **Artifacts**: RandomForest model, KMeans model, feature columns

**Also visible:**
- **`content-insights-inference`** experiment (1 run)
  - Logged during backend startup
  - Shows predictive model diagnostics

**Talk points:**
- "Training logged via `scripts/train_pipeline.py`"
- "Backend inference also tracked (optional)"
- "Model versioning + artifact storage"
- "Compare runs and select best model"

---

## Full Demo Walkthrough (10 minutes)

### Setup Phase (3 min)
1. **Choose mode:**
   ```bash
   # Option A: Docker (simpler for audience)
   ./docker-demo.sh up
   
   # Option B: Tmux (better for technical deep dive)
   ./demo.sh
   ```

2. **Wait for services** (~1 minute for Docker, ~30 sec for Tmux)

3. **IMPORTANT: Populate MLflow with training data** (this step is crucial!)
   
   **For Docker mode:**
   ```bash
   # In a new terminal
   cd <repo-root>
   source .venv/bin/activate
   MLFLOW_TRACKING_URI=http://localhost:5000 python -m scripts.train_pipeline
   # Wait ~30 seconds for "✓ MLflow tracking complete"
   ```
   
   **For Tmux mode:** (Already included—watch the Training Pipeline pane)

### Presentation Phase (7 min)

**Part 1: Data Pipeline (2 min)**
- Show frontend dashboard at http://localhost:5173
- Point to metrics: "1,000 videos analyzed"
- Show cluster visualization: "Algorithm found 2 distinct audience segments"
- Show anomalies: "Detected 100+ unusual performance patterns"

**Part 2: ML Models (3 min)**
- Click into Backend Docs: http://localhost:8000/docs
- Show `/metrics` endpoint response
- Explain: "Clustering (K-Means), Anomalies (Isolation Forest), Predictions (RandomForest + MAPIE)"
- Demo `/similar` endpoint: "TF-IDF embeddings for content recommendations"

**Part 3: MLflow Integration (3 min)**
- Open MLflow UI: http://localhost:5000
- Navigate to **Experiments** → **`content-insights-training`**
- Show 5 training runs
- Click one run, show:
  - Parameters logged
  - Metrics (R² = 0.99+)
  - Artifacts (model files)
- Explain: "Every training run tracked for reproducibility"
- Show **`content-insights-inference`** experiment: "Backend also logs prediction metrics"

**Wrap-up:**
- "Full ML pipeline: training → versioning → inference → UI"
- "Production-ready with Docker deployment"

---

## Architecture & Code References

### Training with MLflow
**File:** [scripts/train_pipeline.py](scripts/train_pipeline.py)

```python
# Set tracking URI
mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI'))
mlflow.set_experiment("content-insights-training")

# Log parameters, metrics, models
mlflow.log_param("n_estimators", 10)
mlflow.log_metric("train_r2", 0.99)
mlflow.sklearn.log_model(rf, "random_forest_model")
```

### Backend with MLflow (Optional)
**File:** [backend/app/analysis_predictive.py](backend/app/analysis_predictive.py)

```python
if MLFLOW_AVAILABLE and MLFLOW_TRACKING_ENABLED:
    mlflow.set_experiment("content-insights-inference")
    mlflow.log_metric("mae", mae)
    mlflow.log_metric("r2", r2)
    mlflow.sklearn.log_model(mapie_model, "predictive_model")
```

### Backend API Startup
**File:** [backend/app/main.py](backend/app/main.py)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    STATE = build_state(...)  # Trains models on startup
    yield
```

### Frontend API Client
**File:** [frontend/src/api/client.ts](frontend/src/api/client.ts)

```typescript
const BASE = env.VITE_API_URL ?? "http://localhost:8000";
export const getInsights = () => fetch(`${BASE}/insights`);
```

---

## Docker Files Reference

### Which file does what?

| File | Purpose | When used |
|------|---------|-----------|
| `docker-compose.prod.yml` | Full demo stack: PostgreSQL + MLflow + Backend + Frontend | `./docker-demo.sh up` |
| `docker-compose.yml` | Dev-only: Backend + Frontend only (no MLflow, no DB) | `docker compose up` (bare) |
| `backend/Dockerfile` | Builds the FastAPI backend image | On `docker compose ... up --build` |
| `frontend/Dockerfile` | Builds the React Vite frontend image | On `docker compose ... up --build` |
| `Dockerfile.training` | Multi-stage build for the training pipeline job | `--profile training` (optional) |

### Why `docker-compose.prod.yml` and not `docker-compose.yml`?

- **`docker-compose.yml`** (dev) — 2 services only: backend + frontend. Uses `.env.development`, no MLflow, no PostgreSQL. For fast local code iteration.
- **`docker-compose.prod.yml`** (demo/prod) — 4 services with PostgreSQL-backed MLflow, healthchecks, and startup ordering. Used by `./docker-demo.sh`.
- Docker defaults to `docker-compose.yml` without `-f`, so the demo script explicitly passes `-f docker-compose.prod.yml`.

### `backend/Dockerfile` — what it does
```dockerfile
FROM python:3.12-slim       # Base Python image
WORKDIR /app
COPY pyproject.toml .       # Install deps from pyproject.toml (includes mlflow, sklearn, etc.)
RUN pip install -e ".[dev]"
COPY app /app/app           # Copy FastAPI source code
EXPOSE 8000
CMD uvicorn app.main:app    # Starts API server
```

### `frontend/Dockerfile` — what it does
```dockerfile
FROM node:20-alpine         # Base Node image
WORKDIR /app
COPY package.json .
RUN npm install             # Install React deps (vite, typescript, etc.)
COPY . .
EXPOSE 5173
CMD npm run dev             # Starts Vite dev server with HMR
```

### `Dockerfile.training` — what it does
Multi-stage build for the optional training job container:
- **Stage 1 (builder)**: installs Python ML packages from `requirements.txt`
- **Stage 2 (runtime)**: copies only the installed packages (smaller image)
- Default command: runs `scripts/train_pipeline.py` via the `--profile training` flag
- Not started automatically by `./docker-demo.sh up` — use the host venv instead (see below)

### `docker-compose.prod.yml` service startup order
```
mlflow-db (PostgreSQL)  →  mlflow (MLflow Server)  →  backend (FastAPI)  →  frontend (React)
  healthcheck: pg_isready     healthcheck: HTTP 5000      healthcheck: HTTP 8000
```
Each service waits for the previous one's healthcheck to pass before starting.

---

## Docker Architecture

### Services in `docker-compose.prod.yml`

```yaml
mlflow-db:        PostgreSQL 15 (port 5432)
                  └─ Stores MLflow run metadata, params, metrics
                  └─ Volume: mlflow_db_data (persists between restarts)

mlflow:           python:3.12-slim running MLflow 2.14.3 (port 5000)
                  └─ Backend store: PostgreSQL (mlflow-db:5432)
                  └─ Artifact root: ./mlruns/artifacts (host volume)
                  └─ Deps pinned: setuptools==80.9.0 (required for pkg_resources)

backend:          Built from backend/Dockerfile — FastAPI (port 8000)
                  └─ Depends on: mlflow (waits for health)
                  └─ MLFLOW_TRACKING_URI: http://mlflow:5000
                  └─ Mounts: sample_videos.csv, models/, mlruns/

frontend:         Built from frontend/Dockerfile — React Vite (port 5173)
                  └─ Depends on: backend
                  └─ VITE_API_BASE_URL: http://localhost:8000
```

### Startup Order
1. PostgreSQL starts (5432)
2. MLflow waits for PostgreSQL health
3. Backend waits for MLflow health
4. Frontend starts (depends on backend)

---

## Troubleshooting

### Docker Issues

**Container won't start:**
```bash
docker compose -f docker-compose.prod.yml logs backend
# Check error, ensure ports 5173, 8000, 5000, 5432 are free
```

**Port already in use:**
```bash
# Find process using port 5000 (MLflow)
lsof -i :5000
kill -9 <PID>

# Or just use Docker, it's isolated
./docker-demo.sh down
./docker-demo.sh up
```

### Tmux Issues

**Tmux not installed:**
```bash
sudo apt-get install tmux
```

**Cannot find venv:**
```bash
./setup_venv.sh
pip install -e backend/
```

**Terminal output garbled:**
```bash
tmux kill-session -t content-insights-demo
./demo.sh  # Restart
```

### MLflow Issues

**No experiments showing:**
```bash
# Docker mode: check via MLflow API (uses PostgreSQL, not file store)
curl -s http://localhost:5000/api/2.0/mlflow/experiments/search | python3 -m json.tool
# Should show content-insights-training and content-insights-inference experiments

# If empty, populate MLflow by running the training pipeline:
source .venv/bin/activate
MLFLOW_TRACKING_URI=http://localhost:5000 python -m scripts.train_pipeline
```

**MLflow container crashes on startup (`pkg_resources` or `EntryPoints` errors):**

This is a Python package version conflict. The `python:3.12-slim` Docker image gets the
latest pip/setuptools, which can break older MLflow versions. The root causes are:

| Error | Root Cause | Fix applied |
|-------|-----------|------------|
| `ModuleNotFoundError: No module named 'pkg_resources'` | `setuptools >= 81` removed `pkg_resources` | Pin `setuptools==80.9.0` before mlflow install |
| `AttributeError: 'EntryPoints' object has no attribute 'get'` | Python 3.12 stdlib `importlib.metadata` dropped dict-style API used by MLflow < 2.14 | Use `mlflow==2.14.3` (last 2.x with modern API) |

**Pinned versions in `docker-compose.prod.yml` (do not change these without testing):**
```yaml
# In the mlflow service command:
pip install setuptools==80.9.0 && pip install mlflow==2.14.3 psycopg2-binary
```

**If you upgrade MLflow in future:**
1. Try `mlflow==2.16.x` (if released) — test in Docker first
2. Do NOT use MLflow 3.x with this codebase — the `/api/2.0/mlflow/logged-models` endpoint doesn't exist in 3.x's server and the local `.venv` client (also 3.x) will throw 404 errors
3. If upgrading: edit the `command:` in `docker-compose.prod.yml` and re-run `./docker-demo.sh up`

**`pkg_resources` deprecation warning (safe to ignore):**
```
UserWarning: pkg_resources is deprecated as an API...
```
This is just a warning from MLflow's internals — the server still runs correctly.

**File store deprecation warning (expected):**
```
The filesystem tracking backend is deprecated as of February 2026.
Consider transitioning to a database backend (e.g., 'sqlite:///mlflow.db')
```
This is normal. Production uses PostgreSQL (Docker).

---

## Demo Scripts Reference

### demo.sh
Starts 4 tmux panes:
1. **Training Pipeline** - Logs training runs to MLflow
2. **Backend API** - FastAPI on port 8000 (auto-reload enabled)
3. **MLflow UI** - Experiment tracking on port 5000
4. **Frontend** - React Vite on port 5173 (HMR enabled)

**Logs visible in real-time within tmux.**

### docker-demo.sh
Commands:
- `./docker-demo.sh up` - Start stack (default)
- `./docker-demo.sh down` - Stop and clean
- `./docker-demo.sh logs` - Show live logs
- `./docker-demo.sh restart` - Restart services

**Services run in containers, isolated from host.**

---

## Quick Commands Reference

### Local Development
```bash
# Setup
./setup_venv.sh
source .venv/bin/activate
pip install -e backend/

# Training with MLflow
MLFLOW_TRACKING_URI=file:./mlruns python -m scripts.train_pipeline

# MLflow UI
mlflow ui --backend-store-uri file:./mlruns --port 5000

# Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

### Docker
```bash
# Full stack
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml down -v
```

### Tmux (if using demo.sh)
```bash
# Attach
tmux attach -t content-insights-demo

# Navigate panes
Ctrl+B → Arrow keys

# Detach
Ctrl+B → D

# Kill
tmux kill-session -t content-insights-demo
```

---

## Next Steps

### For Presenters
- [ ] Test `./docker-demo.sh up` in advance
- [ ] Have 3 browser tabs ready (frontend, backend, MLflow)
- [ ] Rehearse talking points (~10 min total)
- [ ] Optional: Run `./demo.sh` once to show tmux workflow

### For Developers
- [ ] Explore [backend/app/](backend/app/) code structure
- [ ] Check [notebooks/01_exploration_v2.ipynb](notebooks/01_exploration_v2.ipynb) for analysis details
- [ ] Review [docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) for architecture overview
- [ ] Modify hyperparameters in [scripts/train_pipeline.py](scripts/train_pipeline.py) and retrain

---

## Support

Errors or questions? Check:
- [README.md](README.md) - Project overview
- [docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md) - Architecture
- [docs/DOCKER_COMPOSE_GUIDE.md](docs/DOCKER_COMPOSE_GUIDE.md) - Detailed Docker setup
- [docs/PYTEST_TESTING.md](docs/PYTEST_TESTING.md) - Testing guide
