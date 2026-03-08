# Content Performance Insights Dashboard - Blenda Labs Take-Home Assignment

## 📋 Assignment Overview

**Candidate**: *[Your Name]*
**Position**: Solutions Engineer
**Submitted**: March 2026

This is a full-stack analytics platform for short-form video performance analysis, built to demonstrate:
- ✅ **Data Engineering**: Robust ETL pipeline with validation and feature engineering
- ✅ **Analytics Methods**: 5+ analysis techniques (clustering, anomaly detection, predictive modeling with uncertainty quantification, trend analysis, similarity search)
- ✅ **ML Engineering**: MAPIE conformal prediction, SHAP explainability, model versioning
- ✅ **Full-Stack Development**: FastAPI backend + React/TypeScript frontend + Docker orchestration
- ✅ **Production Practices**: Pre-commit hooks, CI/CD, comprehensive testing, monitoring readiness

**Key Technologies**: Python 3.12, FastAPI, React, TypeScript, Vite, scikit-learn, MAPIE, SHAP, Docker, pytest

---

## 🚀 Quick Start - Testing Before GitHub Push

**IMPORTANT**: Follow this complete testing workflow before pushing to ensure everything works for reviewers.

### Prerequisites

- Docker 20.10+ and Docker Compose v2+ installed
- Python 3.11+ (for local testing)
- Git initialized repository
- 8GB RAM minimum for Docker services

### Step-by-Step Testing Guide

#### **Step 1: Verify Environment**

```bash
# Navigate to project root
cd test_blenda_takehome

# Check Docker availability
docker --version                    # Should show 20.10+
docker compose version              # Should show v2.x (note: no hyphen)

# Verify project files
ls -la                              # Should see: main.py, docker-compose.yml, README.md
ls models/*.joblib | wc -l          # Should show 10+ model files
```

#### **Step 2: Run Pre-Commit Quality Checks**

```bash
# Install quality tools (one-time setup)
make quality-tools

# Install pre-commit hooks
make precommit-install

# Run comprehensive pre-push validation
# This runs: linting, tests, notebook validation, Docker smoke checks
make prepush
```

**Expected Output**:
```
✓ flake8 checks: 0 fatal errors
✓ black formatting: OK
✓ isort imports: OK
✓ mypy types: checked (warnings OK)
✓ pytest: 5/5 tests passed
✓ notebook validation: executed successfully
✓ docker smoke tests: backend + frontend healthy
═══════════════════════════════════════════════
Pre-push quality gate passed.
```

#### **Step 3: Docker Full Stack Test (Recommended)**

This is the **primary validation method** for reviewers - tests exactly what they'll see.

```bash
# Clean any existing containers
docker compose down -v

# Build and start services (detached mode)
docker compose up --build -d

# Wait 30 seconds for services to initialize
sleep 30

# Check service status
docker compose ps                   # Both backend/frontend should be "running"

# View logs for troubleshooting
docker compose logs backend | tail -20
docker compose logs frontend | tail -20

# Test backend health endpoint
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Test backend metrics (verifies models loaded)
curl http://localhost:8000/metrics | jq .model_version
# Expected: "v2" or similar version string

# Test backend API docs (open in browser or curl)
curl -I http://localhost:8000/docs
# Expected: HTTP/1.1 200 OK

# Test frontend (open in browser)
curl -I http://localhost:5173
# Expected: HTTP/1.1 200 OK

# Run backend tests inside container
docker compose exec backend pytest tests/ -v
# Expected: 5 passed

# **Open browser and verify dashboard**
# Visit: http://localhost:5173
# Should see: KPI cards, cluster scatter, anomaly table, predictive panel
```

#### **Step 4: Test Frontend Interactivity** (Browser)

Open http://localhost:5173 and verify:

1. **Overview Panel**: KPI cards show metrics (avg engagement, total views, etc.)
2. **Filters Bar**: Category/thumbnail dropdowns work, date range updates data
3. **Cluster Scatter**: Points are colored by cluster, hover shows video details
4. **Anomaly Table**: Shows videos with anomaly scores, sortable columns
5. **Similar Content**: Select a video, see top-5 similar recommendations
6. **Predictive Panel**:
   - Model metrics visible (R², MAE, etc.)
   - Predicted vs Actual scatter plot
   - MAPIE confidence intervals chart
   - SHAP beeswarm plot
   - Feature importance bar chart

#### **Step 5: Cleanup Docker Test**

```bash
# Stop and remove all containers
docker compose down -v

# (Optional) Remove built images to free space
docker rmi test_blenda_takehome-backend test_blenda_takehome-frontend
```

#### **Step 6: Local Python Test** (Optional - for debugging)

Only needed if Docker tests fail or you want to debug specific issues.

```bash
# Create virtual environment
./setup_venv.sh
source .venv/bin/activate

# Install backend in editable mode
pip install -e backend/

# Run backend tests locally
cd backend && pytest tests/ -v && cd ..

# (Optional) Start backend manually
export APP_DATA_PATH=./sample_videos.csv
cd backend && uvicorn app.main:app --reload &
cd ..

# Test API
curl http://localhost:8000/health

# (Optional) Start frontend
cd frontend && npm install && npm run dev &
cd ..

# Visit http://localhost:5173 in browser

# Cleanup: kill processes when done
pkill -f uvicorn
pkill -f vite
deactivate
```

#### **Step 7: Production Docker Compose Test** (Optional)

Tests production configuration with MLflow tracking.

```bash
# Start production stack
docker compose -f docker-compose.prod.yml up --build -d

# Verify services
docker compose -f docker-compose.prod.yml ps

# Test endpoints
curl http://localhost:8000/health    # Backend
curl -I http://localhost:80          # Frontend (production port 80)
curl -I http://localhost:5000        # MLflow UI

# Cleanup
docker compose -f docker-compose.prod.yml down -v
```

#### **Step 8: Final Pre-Push Checklist**

Before `git push`, verify:

- [ ] Docker compose test passed (Step 3) ✅
- [ ] All 5 pytest tests pass ✅
- [ ] Dashboard opens and all panels render ✅
- [ ] No sensitive files committed (check `.gitignore`)
- [ ] Models directory committed (`.joblib` files present)
- [ ] `make prepush` completes successfully ✅
- [ ] This README accurately describes your implementation
- [ ] Screenshots exist and match README references

```bash
# Final verification commands
git status                          # Check for unexpected files
ls models/*.joblib                  # Verify models present
grep -r "API_KEY\|SECRET\|PASSWORD" --exclude-dir=.git  # Check for leaked secrets
docker compose up --build -d && sleep 30 && \
  curl -f http://localhost:8000/health && \
  curl -I http://localhost:5173 && \
  docker compose down -v            # All-in-one smoke test
```

---

## 📦 Setup

### Runtime Requirements
- Python `>=3.11`
- Node.js `>=20`
- npm
- Docker + Docker Compose (optional)

### Local Execution Path

```bash
git clone <your-repo-url>
cd test_blenda_takehome
./setup_venv.sh
source .venv/bin/activate
```

Execute notebook pipeline (feature engineering + model diagnostics + artifact generation):

```bash
jupyter lab
# Run notebooks/01_exploration_v2.ipynb (Run All)
```

Start backend service:

```bash
cd backend
export APP_DATA_PATH=../sample_videos.csv
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Start frontend service:

```bash
cd frontend
npm install
npm run dev
```

Service endpoints:
- Frontend: `http://localhost:5173`
- Backend OpenAPI: `http://localhost:8000/docs`

### Containerized Execution

Development compose:

```bash
docker-compose up --build
```

Production-oriented compose:

```bash
docker-compose -f docker-compose.prod.yml up --build
```

## Approach

The implementation is intentionally mapped to the three assignment pillars.

### Part 1: Data Processing

Core ETL is implemented in `backend/app/etl.py` with explicit schema and quality controls.

Processing stages:
- Required-column validation against a fixed schema contract.
- Type normalization (`publish_date` -> datetime, metric columns -> numeric with coercion).
- Row-level filtering for invalid domain values (`views > 0`, non-negative engagement counters).
- Deterministic feature derivation:
- `engagement_rate = (likes + comments + shares) / views`
- `avg_watch_time_per_view = watch_time_seconds / views`
- `like_rate`, `comment_rate`, `share_rate`
- Calendar/title structural features (`publish_year`, `publish_month`, `publish_weekday`, `title_length`, `title_words`).

Notebook (`notebooks/01_exploration_v2.ipynb`) extends this with additional analysis features such as `virality_score`, `virality_rate`, and `days_since_publish`.

### Part 2: Insights and Analysis

Implemented analytics methods (assignment asks for at least two):
- Clustering: KMeans plus DBSCAN for centroidal and density-based segmentation.
- Trend/correlation analysis: aggregated and rank-based associations.
- Embeddings/similarity: TF-IDF retrieval with optional semantic embedding extension.
- Anomaly detection: IsolationForest outlier scoring.
- Predictive modeling: RandomForest regression with MAPIE Jackknife+/CrossConformal uncertainty intervals.

### Part 3: Visualization

Interactive dashboard is implemented as a typed React SPA:
- KPI overview cards.
- Dynamic filter controls (category, thumbnail style, date window).
- Clustering panel.
- Anomaly inspection table.
- Similar-content recommendation panel.
- Predictive diagnostics and uncertainty visualization.

---

## 📸 Dashboard Showcase

The interactive dashboard provides comprehensive visual analytics across multiple analytical dimensions:

### 🎯 Predictive Model + MAPIE Jackknife+ Intervals

Complete predictive modeling interface featuring:
- **Model Performance**: Predicted vs Actual engagement with R² score and error metrics
- **Conformal Prediction Intervals**: MAPIE Jackknife+ uncertainty quantification with 90% coverage
- **Residual Diagnostics**: Heteroscedasticity checks and residual distribution analysis
- **Feature Importance**: Permutation-based feature ranking showing critical prediction drivers
- **SHAP Beeswarm**: Individual prediction explanations with feature value color coding (blue=low, red=high)

![Predictive Model Overview](screenshots/images/screenshot_dashboardtop.png)
*Full predictive model dashboard with performance metrics, residual diagnostics, and MAPIE confidence intervals*

### 🎯 Feature Importance & SHAP Explainability

Advanced model interpretation with symmetric layout:
- **Permutation Importance**: Which features are most critical when removed
- **SHAP Beeswarm Plot**: Individual prediction impact visualization showing how feature values (blue=low, red=high) drive engagement predictions
- **Interactive Tooltips**: Detailed per-sample SHAP values and feature characteristics

![Feature Importance & SHAP Beeswarm](screenshots/images/screenshot_dashboard_middle.png)
*Side-by-side comparison of permutation feature importance and SHAP value distributions*

### 📊 Model Performance Metrics & Confidence

Comprehensive model evaluation and uncertainty quantification:
- **Performance Metrics**: MAE, R² score, interval accuracy, confidence levels
- **Interval Hit-Rate**: 100% coverage with MAPIE Jackknife+ conformal prediction
- **Error Distribution**: Histogram analysis for residual normality checks

![Model Performance Metrics](screenshots/images/screenshot_dasbboard_model_end.png)
*Model metrics dashboard with confidence intervals and statistical validation*

---

### Methodology Details Requested During Review

- Elbow/silhouette analysis:
- KMeans grid search over `k=2..10`.
- Silhouette optimum at `k=2`; elbow inflection near `k=4`.
- Operational choice: use finer segmentation where business interpretability benefits from more clusters.

- Train/validation/test protocol:
- Two-stage split in notebook: `60/20/20` using deterministic random seeds.
- RMSE behavior: train error below val/test; val and test close to each other, indicating stable holdout behavior.

- Hyperparameter optimization status:
- Clustering includes explicit `k` search.
- Predictive model currently uses fixed RF configuration (not full search via GridSearch/RandomizedSearch/Optuna).

- `2024-01-01` reference date:
- Used as fixed analysis anchor for `days_since_publish`.
- Advantage: reproducibility.
- Limitation: should be made configurable to avoid date drift/interpretation issues on future datasets.

### Data Leakage and Overfitting Assessment

Controls present:
- Holdout-based validation and separate test slice in notebook.
- Reproducible seeds.
- Conformal calibration with CV-backed uncertainty quantification.
- Residual diagnostics and post-fit validation plots.

Current limitation:
- Target (`engagement_rate`) and several predictors share engagement primitives (`likes/comments/shares` and derivatives), creating leakage risk and optimistic predictive metrics for true forecasting use-cases.

Mitigation path:
- Introduce strict pre-publish feature mode using only covariates available before outcome realization.

## Key Insights

- Performance segments are separable under both centroid and density clustering perspectives.
- Engagement-derived variables dominate explanatory power in current model formulation.
- Conformal intervals provide decision-grade uncertainty bounds beyond point estimates.
- IsolationForest surfaces candidate over- and under-performing outliers for editorial review.
- Title-similarity retrieval provides actionable nearest-neighbor inspiration for content ideation.

## Technical Decisions

### Stack Selection Rationale

- FastAPI: low-friction typed HTTP layer with built-in OpenAPI schema generation.
- React: composable UI model aligned with panelized analytics dashboards.
- Vite: fast cold-start and HMR for rapid frontend iteration.
- TypeScript: compile-time interface checks for API payload correctness.
- pandas/scikit-learn/MAPIE/SHAP: pragmatic analytical stack with explainability and uncertainty support.

### Frontend Architecture (React + Vite + TypeScript)

Runtime composition:
- `frontend/src/main.tsx`: application bootstrap and root mounting.
- `frontend/src/App.tsx`: orchestration layer for stateful data fetching and cross-panel coordination.
- `frontend/src/api/client.ts`: transport abstraction over `fetch`, parameterized by `VITE_API_URL`.
- `frontend/src/types.ts`: DTO/type contract definitions synchronized with backend JSON shape.
- `frontend/src/components/*.tsx`: feature-isolated UI modules.

Component-level responsibilities:
- `frontend/src/components/Overview.tsx`: aggregate KPI rendering.
- `frontend/src/components/FiltersBar.tsx`: controlled inputs -> query parameter generation.
- `frontend/src/components/ClusterScatter.tsx`: cluster visualization and selection behavior.
- `frontend/src/components/AnomaliesTable.tsx`: tabular anomaly inspection.
- `frontend/src/components/SimilarPanel.tsx`: nearest-neighbor recommendation interaction.
- `frontend/src/components/PredictivePanel.tsx`: metrics, residual diagnostics, and interval plots.

Build/deploy integration:
- `frontend/vite.config.ts`: React plugin + dev server configuration.
- `frontend/package.json` scripts:
- `npm run dev`: local development with HMR.
- `npm run build`: production bundle emission.
- `npm run preview`: local serving of built artifacts.

### File/Folder Responsibilities

| Path | Responsibility |
|---|---|
| `notebooks/01_exploration_v2.ipynb` | Experimental and diagnostic pipeline (EDA, feature engineering, model evaluation) |
| `backend/app/main.py` | API entrypoint and route handlers |
| `backend/app/service.py` | Pipeline orchestration and insight payload assembly |
| `backend/app/etl.py` | Data ingestion, cleaning, validation, feature derivation |
| `backend/app/analysis_clustering.py` | KMeans/DBSCAN clustering logic |
| `backend/app/analysis_predictive.py` | RandomForest + MAPIE conformal inference path |
| `backend/app/analysis_anomaly.py` | IsolationForest anomaly detection |
| `backend/app/analysis_embeddings.py` | Text vectorization and similarity utilities |
| `backend/app/analysis_trends.py` | Correlation and trend analytics |
| `backend/app/model_versioning.py` | Model artifact version bookkeeping |
| `backend/tests/` | Automated API/ETL/pipeline validation |
| `frontend/src/` | Typed React SPA implementation |
| `models/` | Persisted model artifacts and manifest files |
| `scripts/train_pipeline.py` | Programmatic training workflow runner |
| `sample_videos.csv` | Assignment input dataset |
| `docker-compose.yml` | Development multi-service orchestration |
| `docker-compose.prod.yml` | Production-oriented service orchestration |
| `setup_venv.sh` | Local Python environment bootstrap |

### Assignment Traceability Matrix

| Requirement | Status | Evidence |
|---|---|---|
| Load and clean data | Complete | `backend/app/etl.py` |
| Derived metrics | Complete | `backend/app/etl.py`, notebook feature engineering cells |
| Validation/error handling | Complete | Schema checks, coercion, and row filtering in ETL |
| At least two analytics methods | Complete | Clustering, anomalies, trends, embeddings, predictive modeling |
| Interactive dashboard | Complete | React dashboard with filters and analysis panels |
| README with setup/approach/insights/decisions/improvements | Complete | This document |

## Given More Time

- Implement leakage-safe forecasting profile (publish-time-only features).
- Add predictive hyperparameter search (RandomizedSearchCV/Optuna) with cross-validated model selection.
- Parameterize and document reference-date strategy (`days_since_publish`).
- Add temporal holdout/rolling-window evaluation to better mirror production forecasting.
- Integrate MLflow in training/inference code paths (`mlflow.start_run`, `log_params`, `log_metrics`, `log_artifact`) so experiment tracking is not only infrastructure-level.
- Add optional LLM-based analysis layer (OpenAI or compatible API) for narrative insight summaries, anomaly explanations, and recommendation text generation with prompt/version logging.
- Expand backend and frontend test coverage with CI gates.
- Add reproducibility checks for notebook outputs and metric drift thresholds.
- Add one-command reviewer harness for end-to-end validation.

---

## Documentation Structure

This repository includes multiple .md files serving different purposes:

| File | Purpose | Status | Use When |
|---|---|---|---|
| [README.md](README.md) | **Primary assignment submission** - Complete setup, approach, insights, decisions | ✅ Current | Reviewing submission requirements |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | **Comprehensive execution guide** - Detailed notebook cell breakdown, architecture diagrams, troubleshooting | ✅ Current | Deep-diving into implementation details |
| [DOCKER_GUIDE.md](DOCKER_GUIDE.md) | **Docker command reference** - Build/run individual services, volume management | ✅ Current | Working with containers directly |
| [DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md) | **Compose orchestration** - Dev vs prod configurations, networking, scaling | ✅ Current | Multi-service deployment |
| [PYTEST_TESTING.md](PYTEST_TESTING.md) | **Unit testing guide** - Test organization, fixtures, coverage targets | ✅ Current | Running/writing tests |
| [MONITORING.md](MONITORING.md) | **Production monitoring** - Prometheus, Grafana, alerting (roadmap) | ⚠️ Roadmap | Planning production observability |
| [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) | **CI/CD templates** - GitHub Actions workflow examples | ✅ Current | Setting up automation |
| [docs/images/README.md](docs/images/README.md) | **Screenshot inventory** - UI documentation references | ✅ Current | Tracking visual assets |

**Note**: `README_OLD.md` was removed (contained outdated k=4 clustering config and conflicting metrics from earlier iteration).

---

## 🧪 Pre-Push Validation Reference

**⚠️ For complete step-by-step testing instructions, see the [Quick Start Testing Guide](#-quick-start---testing-before-github-push) at the top of this README.**

### Quick Reference Commands

```bash
# One-command quality gate (recommended before any push)
make prepush

# Docker smoke test
# Docker smoke test
docker compose up --build -d && sleep 30 && \
  curl -f http://localhost:8000/health && curl -I http://localhost:5173 && \
  docker compose down -v

# Manual pre-commit hook check
make precommit-run

# Local pytest only
cd backend && pytest tests/ -v && cd ..
```

### 🚨 Common Issues Reference

| Issue | Solution |
|---|---|
| `docker-compose: command not found` | Use `docker compose` (v2 syntax without hyphen) |
| Port 8000/5173 already in use | `docker compose down`, or kill: `lsof -ti:8000 \| xargs kill -9` |
| Backend test failures | Verify `models/` directory exists with `.joblib` files |
| Frontend blank screen | Check browser console; verify `VITE_API_URL` in network tab |
| CORS errors | Backend configured for localhost origins (see `settings.py`) |
| `make: command not found` | Install make: `sudo apt install make` (Ubuntu/Debian) |
| Models not loading | Run notebook first: `jupyter lab` → execute `01_exploration_v2.ipynb` |

For detailed troubleshooting, see the [Step-by-Step Testing Guide](#-quick-start---testing-before-github-push) above.

---

## 📦 Detailed Setup Instructions
