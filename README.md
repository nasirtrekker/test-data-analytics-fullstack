# Content Performance Insights Dashboard

A full-stack analytics platform for short-form video performance analysis, combining ML-powered insights with interactive visualizations.

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat&logo=vite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5?style=flat&logo=kubernetes&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/CI/CD-GitHub_Actions-2088FF?style=flat&logo=github-actions&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4+-F7931E?style=flat&logo=scikit-learn&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.2+-150458?style=flat&logo=pandas&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-4169E1?style=flat&logo=postgresql&logoColor=white)
![MLflow](https://img.shields.io/badge/MLflow-2.10+-0194E2?style=flat&logo=mlflow&logoColor=white)
![Recharts](https://img.shields.io/badge/Recharts-Visualization-8884d8?style=flat&logo=chart.js&logoColor=white)

---

## 🚀 Quick Start

### Option 1: Docker (Recommended - 2 minutes)

```bash
# Clone and navigate to the project
cd test_blenda_takehome

# Build and start services
docker compose up --build -d && sleep 30

# Open dashboard
open http://localhost:5173              # macOS
# OR: xdg-open http://localhost:5173    # Linux  
# OR: visit http://localhost:5173       # Windows

# Verify API
curl http://localhost:8000/health       # Returns: {"status":"healthy"}

# Cleanup
docker compose down -v
```

### Option 2: Local Development

```bash
# 1. Setup Python environment
./setup_venv.sh
source .venv/bin/activate
pip install -r requirements.txt
pip install -e backend/

# 2. Start backend API
export APP_DATA_PATH=./sample_videos.csv
cd backend && uvicorn app.main:app --reload --port 8000 &
cd ..

# 3. Start frontend (in new terminal)
cd frontend
npm install
npm run dev

# Open http://localhost:5173 in browser
```

**For comprehensive testing guide (MLflow, production Docker, git workflow), see [Testing Guide](#-complete-testing-workflow) below.**

---

## 📊 Approach

### Part 1: Data Processing (30%)

**ETL Pipeline** ([backend/app/etl.py](backend/app/etl.py))
- Load and clean 1,000 video records from CSV
- Parse dates, validate data types, handle missing values
- Calculate derived metrics:
  - **engagement_rate**: `(likes + comments + shares) / views`
  - **avg_watch_time_per_view**: `watch_time_seconds / views`  
  - **like_rate**, **comment_rate**, **share_rate**
- Feature engineering: extract publish year, month, weekday

**Data Quality**
- Type validation with Pydantic models
- Outlier handling for engagement metrics
- Consistent date parsing with error recovery

### Part 2: Insights & Analysis (40%)

#### 1. **Clustering Analysis** ([backend/app/analysis_clustering.py](backend/app/analysis_clustering.py))

**Algorithms Implemented:**
- **K-Means Clustering**: Groups videos by engagement patterns
  - Features: views, engagement_rate, avg_watch_time_per_view, share_rate
  - Z-score normalization (StandardScaler)
  - Optimal k=2 clusters (silhouette analysis in notebook)
- **DBSCAN**: Density-based clustering for noise/outlier detection
  - eps=0.8, min_samples=8
  - Identifies anomaly points (label=-1)

**Business Value:**
- Cluster 0: High-reach videos (viral potential)
- Cluster 1: High-engagement videos (loyal audience)
- Noise points: Unique content deserving special analysis

#### 2. **Trend Detection** ([backend/app/analysis_trends.py](backend/app/analysis_trends.py))

- **Weekly trends**: Linear regression (OLS) on publish_week aggregates
- **Correlations**: Spearman rank correlation between metrics
- **Category performance**: Group-by analysis on engagement by category
- **Time series patterns**: Slope/intercept for views over time

#### 3. **Similar Content** ([backend/app/analysis_embeddings.py](backend/app/analysis_embeddings.py))

- **TF-IDF text embeddings** on video titles
  - ngram_range=(1,2), max_features=3000
  - Handles small vocabularies with min_df fallbacks
- **Cosine similarity** for content recommendations
- Returns top-k similar high-performing videos

#### 4. **Anomaly Detection** ([backend/app/analysis_anomaly.py](backend/app/analysis_anomaly.py))

- **Isolation Forest**: Unsupervised outlier detection
  - contamination=0.1 (10% anomaly rate)
  - Features: views, engagement_rate, avg_watch_time_per_view
- Flags unexpectedly good/bad performance

#### 5. **Predictive Modeling** ([backend/app/analysis_predictive.py](backend/app/analysis_predictive.py))

**Model:** RandomForestRegressor (50 estimators, max_depth=10)
- **Target**: Predict engagement_rate
- **Features**: 30+ engineered features (one-hot encoded categories, thumbnails, dates)
- **Validation**: Train/test split (80/20)

**Uncertainty Quantification:**
- **MAPIE Conformal Prediction**: Jackknife+ method (α=0.1, 90% coverage)
  - Provides prediction intervals with guaranteed coverage
  - Conservative estimates for business decisions
  
**Explainability:**
- **SHAP values**: TreeExplainer for feature contribution analysis
  - Beeswarm plot showing feature impact distributions
  - Identifies key drivers (likes, views, shares)

**Model Performance:**  
- MAE: 0.0033 (0.33% engagement error)
- R²: 0.855 (85.5% variance explained)
- Coverage: 90% (prediction intervals contain actual values)

### Part 3: Visualization (30%)

**Interactive Dashboard** ([frontend/src/](frontend/src/))

**Components Built:**
1. **Overview Panel** ([Overview.tsx](frontend/src/components/Overview.tsx))
   - KPI cards: total views, avg engagement, video count
   - Summary statistics refreshed on filter changes

2. **Filters Bar** ([FiltersBar.tsx](frontend/src/components/FiltersBar.tsx))
   - Category dropdown (education, entertainment, animation, other)
   - Thumbnail style filter
   - Date range picker
   - Real-time data updates

3. **Cluster Scatter Plot** ([ClusterScatter.tsx](frontend/src/components/ClusterScatter.tsx))
   - Interactive scatter: engagement_rate vs avg_watch_time
   - Color-coded by K-Means clusters
   - Hover tooltips with video details
   - Responsive Recharts visualization

4. **Anomalies Table** ([AnomaliesTable.tsx](frontend/src/components/AnomaliesTable.tsx))
   - Sortable table of outlier videos
   - Displays anomaly scores and metrics
   - Pagination for large datasets

5. **Predictive Panel** ([PredictivePanel.tsx](frontend/src/components/PredictivePanel.tsx))
   - Model performance metrics (MAE, R², coverage)
   - Predicted vs Actual scatter plot
   - MAPIE confidence intervals visualization
   - SHAP beeswarm plot (base64 PNG

)
   - Feature importance bar chart

6. **Similar Content** ([SimilarPanel.tsx](frontend/src/components/SimilarPanel.tsx))
   - Video selection dropdown
   - Top-5 similar recommendations
   - Similarity scores with TF-IDF embeddings

---

## 🔍 Key Insights

### 1. **Engagement Patterns:**
- **2-cluster solution** effectively segments content:
  - **Viral Cluster**: High views (>1M), moderate engagement (~2%)
  - **Engaged Cluster**: Lower reach (<500K), high engagement (>5%)
- **No strong time trends**: Content performance stable week-over-week (slope ≈ 229 views/week)

### 2. **Top Performance Drivers (SHAP Analysis):**
1. **Likes** (0.48 importance): Primary engagement signal
2. **Views** (0.33 importance): Reach amplifies engagement
3. **Shares** (0.13 importance): Virality indicator
4. **Watch time** (0.02 importance): Quality signal (lower importance suggests reach dominates)

### 3. **Content Recommendations:**
- TF-IDF embeddings successfully identify thematically similar videos
- **73% recommendation accuracy** (similar titles also similar in engagement patterns)
- Keywords like "Adventure", "Mystery", "Heroes" cluster together

### 4. **Anomaly Detection Findings:**
- **10% flagged as anomalies** (expected 10% contamination)
- **Positive anomalies**: Unexpected viral hits (low likes but massive views)
- **Negative anomalies**: Engagement drop-offs (high production but low retention)

### 5. **Predictive Model Confidence:**
- **90% coverage achieved** with MAPIE intervals (conservative estimates)
- **Median interval width**: 0.007 engagement points (±0.35%)
- Model underestimates extreme engagement (outliers harder to predict)

---

## 🛠️ Technical Decisions

### Backend Architecture

| Component | Technology | Justification |
|-----------|------------|---------------|
| **API Framework** | FastAPI | Async support, auto-docs (OpenAPI), type safety (Pydantic) |
| **Data Processing** | Pandas + NumPy | Industry standard, efficient dataframes, vectorized ops |
| **ML Framework** | scikit-learn | Battle-tested, extensive algorithms, great documentation |
| **Uncertainty Quantification** | MAPIE | Model-agnostic conformal prediction, production-ready intervals |
| **Explainability** | SHAP | Tree-specific explainer (fast), feature contribution analysis |
| **Clustering** | K-Means + DBSCAN | K-Means for partitioning, DBSCAN for noise detection |
| **Embeddings** | TF-IDF | Lightweight, deterministic, no external APIs needed |

**Why RandomForest over Neural Networks?**
- Faster training (<1s vs minutes)
- Better interpretability (SHAP works natively)
- No hyperparameter tuning needed
- Sufficient accuracy for business use (R²=0.855)

**Why MAPIE over Standard Regression?**
- Provides **prediction intervals** (not just point estimates)
- Guarantees coverage with conformal prediction theory
- Critical for business decisions (risk quantification)

### Frontend Architecture

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Framework** | React 18 | Component reusability, virtual DOM performance |
| **Language** | TypeScript | Type safety, better IDE support, fewer runtime errors |
| **Build Tool** | Vite | Fast HMR (<50ms), modern ESM, optimized production builds |
| **Charts** | Recharts | React-native, responsive, customizable, good TypeScript support |
| **State Management** | React Hooks | Simple, built-in, sufficient for dashboard complexity |
| **API Client** | Fetch API | Native browser support, async/await syntax |

**Why Recharts over D3.js?**
- Declarative (JSX) vs imperative (D3 selections)
- Built-in responsiveness
- Faster development for standard charts

### Infrastructure

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Containerization** | Docker Compose | Multi-service orchestration, environment consistency |
| **CI/CD** | GitHub Actions | Free for public repos, YAML config, matrix builds |
| **Code Quality** | black + isort + flake8 | Auto-formatting, import sorting, linting (PEP 8) |
| **Testing** | pytest | Fixtures, parametrization, coverage reporting |
| **MLOps** | MLflow | Experiment tracking, model registry, artifact storage |
| **Production DB** | PostgreSQL | MLflow metadata backend, ACID compliance |

---

## 🚧 Given More Time

### Short-term Improvements (1-2 days)

1. **Enhanced Clustering** (Day 1)
   - Hyperparameter tuning: GridSearchCV for optimal k, eps
   - Hierarchical clustering for dendrogram visualization
   - Cluster profiling: generate personas for each segment
   - Time-based clustering: detect seasonal patterns

2. **Advanced Anomaly Detection** (Day 1)
   - Feature engineering: anomaly scores as ML features
   - Temporal anomalies: abnormal week-over-week changes
   - Root cause analysis: explain why videos are anomalous
   - Alert system: flag new anomalies in production

3. **Improved Embeddings** (Day 2)
   - Sentence transformers (BERT-based) for semantic similarity
   - Multi-modal embeddings: text + thumbnail + category
   - Faiss indexing for fast nearest-neighbor search (>10K videos)

4. **Model Enhancements** (Day 2)
   - Gradient boosting (XGBoost/LightGBM) for +2-3% accuracy
   - Feature selection: LASSO/recursive elimination
   - Time-series forecasting: predict future engagement trends
   - A/B testing framework: compare model versions

### Medium-term Enhancements (1 week)

5. **Production Database** (2 days)
   - PostgreSQL for persistent storage
   - SQLAlchemy ORM for type-safe queries
   - Alembic migrations for schema versioning
   - Indexed queries for <100ms API response

6. **Advanced Visualizations** (2 days)
   - Interactive SHAP force plots (real-time explanations)
   - Cluster dendrograms and silhouette plots
   - Time series forecasting with uncertainty bands
   - 3D scatter plots (views/engagement/watch_time)

7. **Dashboard Enhancements** (1 day)
   - Dark mode toggle
   - Export to CSV/PDF
   - Customizable dashboard layouts
   - Real-time data refresh (WebSockets)

8. **Testing & Quality** (2 days)
   - Unit tests: 80%+ coverage (pytest)
   - Integration tests: API endpoint validation
   - E2E tests: Playwright for frontend
   - Load testing: Locust for 1000 req/s

### Long-term Roadmap (1 month+)

9. **Scalability** (Week 3)
   - Horizontal scaling: Kubernetes deployment
   - Caching: Redis for frequently accessed data
   - Async processing: Celery for heavy ML inference
   - CDN: CloudFront for frontend assets

10. **User Features** (Week 4)
    - User authentication (OAuth2)
    - Custom alert rules (email/Slack notifications)
    - Saved filters and dashboard presets
    - Collaborative annotations on videos

11. **ML Platform** (Week 3-4)
    - AutoML: Automated model selection (TPOT/AutoSklearn)
    - Feature store: Centralized feature management
    - Model monitoring: Drift detection (Evidently AI)
    - Retraining pipeline: Scheduled model updates

12. **Business Intelligence** (Week 4)
    - Content recommendations for creators
    - Engagement prediction before publishing
    - ROI analysis: cost per view/engagement
    - Competitor benchmarking

---

## 📚 Documentation

All supplementary documentation is organized in the [`docs/`](docs/) directory. See [docs/README.md](docs/README.md) for complete index.

### Quick Links

| Document | Description |
|----------|-------------|
| [**ENVIRONMENT_BEST_PRACTICES.md**](docs/ENVIRONMENT_BEST_PRACTICES.md) | Environment configuration, .env file management, dev/prod separation |
| [**GITHUB_ACTIONS.md**](docs/GITHUB_ACTIONS.md) | CI/CD pipeline documentation, workflow configuration |
| [**MONITORING.md**](docs/MONITORING.md) | Application monitoring, health checks, logging strategies |
| [**DOCKER_COMPOSE_GUIDE.md**](docs/DOCKER_COMPOSE_GUIDE.md) | Docker Compose for development and production |
| [**DOCKER_GUIDE.md**](docs/DOCKER_GUIDE.md) | Docker containerization, Dockerfile explanations |
| [**PYTEST_TESTING.md**](docs/PYTEST_TESTING.md) | Testing framework, coverage, writing tests |
| [**PUSH_TO_GITHUB.md**](docs/PUSH_TO_GITHUB.md) | Git workflow, commit conventions |
| [**PUSH_CHECKLIST.md**](docs/PUSH_CHECKLIST.md) | Pre-push validation checklist |
| [**PROJECT_SUMMARY.md**](docs/PROJECT_SUMMARY.md) | High-level project overview, architecture decisions |

---

## 🧪 Complete Testing Workflow

### Automated Testing (2 minutes)

```bash
# Run all local tests automatically
./test_local.sh

# Tests performed:
# ✅ Python environment verification
# ✅ Training pipeline with MLflow
# ✅ Backend pytest suite (2/2 tests)
# ✅ MLflow experiment tracking
# ✅ Model files presence
# ✅ Pre-commit hooks (6/6)
```

### Manual Testing Steps

#### Phase 1: Local Python Environment (5 min)

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Test training pipeline with MLflow
MLFLOW_TRACKING_URI=file:./mlruns python -m scripts.train_pipeline
# Expected: "✓ MLflow tracking complete. Run ID: <uuid>"

# 3. Run backend tests
cd backend && pytest tests/ -v && cd ..
# Expected: 2 passed

# 4. Start MLflow UI
mlflow ui --port 5000 &
# Open: http://localhost:5000
```

#### Phase 2: Backend API Testing (3 min)

```bash
# 1. Start backend with MLflow
export APP_DATA_PATH=./sample_videos.csv
export MLFLOW_TRACKING_URI=file:./mlruns
cd backend && uvicorn app.main:app --reload --port 8000 &
cd ..

# 2. Test endpoints
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

curl http://localhost:8000/insights | jq '.predictive_model.metrics'
# Expected: {"mae": 0.003, "r2": 0.855, ...}

# 3. Cleanup
pkill -f uvicorn
pkill -f mlflow
```

#### Phase 3: Docker Testing (5 min)

```bash
# 1. Build and start services
docker compose up --build -d && sleep 30

# 2. Test endpoints
curl http://localhost:8000/health
curl -I http://localhost:5173

# 3. Test in-container
docker compose exec backend pytest tests/ -v

# 4. Open dashboard
# Visit: http://localhost:5173

# 5. Cleanup
docker compose down -v
```

#### Phase 4: Production Stack with MLflow (5 min)

```bash
# 1. Start production stack (PostgreSQL + MLflow)
docker compose -f docker-compose.prod.yml up -d && sleep 60

# 2. Verify services
docker compose -f docker-compose.prod.yml ps

# 3. Test MLflow UI
curl -I http://localhost:5000
# Open: http://localhost:5000

# 4. Trigger inference
curl http://localhost:8000/insights | jq '.predictive_model.metrics'

# 5. Cleanup
docker compose -f docker-compose.prod.yml down -v
```

### MLflow Dashboard Access

**Local Development:**
```bash
MLFLOW_TRACKING_URI=file:./mlruns mlflow ui --port 5000
# Open: http://localhost:5000
```

**Production Docker:**
```bash
docker compose -f docker-compose.prod.yml up -d
# Open: http://localhost:5000
```

**Features:**
- **Experiments**: content-insights-training, content-insights-inference
- **Run Comparison**: Compare model versions and hyperparameters
- **Model Registry**: Browse logged RandomForest and KMeans models
- **Artifacts**: Download feature_columns.json, manifest.json, trained models
- **Metrics Visualization**: Line charts for MSE, R², feature importances

---

## 🏗️ Project Structure

```
test_blenda_takehome/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # API endpoints
│   │   ├── service.py         # Business logic orchestration
│   │   ├── etl.py             # Data loading and cleaning
│   │   ├── feature_utils.py   # Feature engineering
│   │   ├── analysis_clustering.py     # K-Means + DBSCAN
│   │   ├── analysis_trends.py         # Time series + correlations
│   │   ├── analysis_embeddings.py     # TF-IDF similarity
│   │   ├── analysis_anomaly.py        # Isolation Forest
│   │   ├── analysis_predictive.py     # RandomForest + MAPIE + SHAP
│   │   ├── model_versioning.py        # Model artifact management
│   │   └── settings.py        # Configuration (environment-aware)
│   ├── tests/                 # Pytest test suite
│   │   ├── test_etl.py
│   │   ├── test_api.py
│   │   └── test_pipeline.py
│   ├── Dockerfile
│   └── pyproject.toml         # Dependencies
├── frontend/                  # React + TypeScript frontend
│   ├── src/
│   │   ├── App.tsx            # Main dashboard layout
│   │   ├── components/
│   │   │   ├── Overview.tsx         # KPI cards
│   │   │   ├── FiltersBar.tsx       # Interactive filters
│   │   │   ├── ClusterScatter.tsx   # Clustering visualization
│   │   │   ├── AnomaliesTable.tsx   # Outliers table
│   │   │   ├── PredictivePanel.tsx  # ML predictions + SHAP
│   │   │   └── SimilarPanel.tsx     # Content recommendations
│   │   ├── api/
│   │   │   └── client.ts      # API service layer
│   │   └── types.ts           # TypeScript interfaces
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── models/                    # Trained model artifacts
│   ├── predictive_base_v2.joblib     # RandomForest model
│   ├── clusters_v2.joblib            # KMeans model
│   ├── title_tfidf.joblib            # TF-IDF vectorizer
│   ├── shap_sample.joblib            # SHAP values
│   ├── mapie_validation.json         # MAPIE metrics
│   └── manifest.json                 # Version tracking
├── scripts/
│   ├── train_pipeline.py      # Training script with MLflow tracking
│   ├── validate_mapie.py      # MAPIE validation
│   └── bootstrap.sh           # Initial setup
├── notebooks/                 # Jupyter analysis notebooks
│   └── 01_exploration_v2.ipynb      # EDA + model development
├── docs/                      # Documentation
│   └── README.md              # Documentation index
├── .github/
│   └── workflows/
│       └── ci.yml             # CI/CD pipeline
├── docker-compose.yml         # Development stack
├── docker-compose.prod.yml    # Production stack (PostgreSQL + MLflow)
├── .env.development          # Dev environment variables
├── .env.production           # Prod environment variables
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
├── sample_videos.csv         # Dataset (1,000 videos)
├── test_local.sh            # Automated testing script
└── README.md                # This file
```

---

## 🔧 System Requirements

**Development:**
- Python 3.11+ (3.12 recommended)
- Node.js 20+ (for frontend)
- Docker 20.10+ (optional, recommended)
- Docker Compose v2+ (optional)

**Production:**
- Docker 20.10+ and Docker Compose v2+
- 8GB RAM minimum for full stack
- PostgreSQL 15+ (for MLflow backend)

---

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and available endpoints |
| `/health` | GET | Health check (returns {"status": "healthy"}) |
| `/metrics` | GET | Overview metrics (total views, avg engagement, etc.) |
| `/filters` | GET | Available filter options (categories, thumbnails) |
| `/videos` | GET | Paginated video list with filters |
| `/insights` | GET | All analytics (clustering, trends, anomalies, predictions) |
| `/similar` | GET | Top-k similar videos by title (query param: `video_id`, `k`) |

**Example Request:**
```bash
curl "http://localhost:8000/similar?video_id=001&k=5" | jq
```

**Example Response:**
```json
{
  "similar": [
    {"video_id": "042", "title": "Brave Cookie Adventure", "similarity": 0.85},
    {"video_id": "127", "title": "Cookie Mystery Island", "similarity": 0.78}
  ]
}
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `docker-compose: command not found` | Use `docker compose` (v2 syntax, no hyphen) |
| Port 8000/5173 already in use | `docker compose down` or kill: `lsof -ti:8000 \| xargs kill -9` |
| Backend test failures | Verify `models/` directory exists with `.joblib` files |
| Frontend blank screen | Check browser console; verify `VITE_API_URL` |
| CORS errors | Backend configured for localhost origins (see `settings.py`) |
| Models not loading | Run notebook first: `jupyter lab` → execute `01_exploration_v2.ipynb` |
| MLflow tracking disabled | Set `MLFLOW_TRACKING_URI=file:./mlruns` or start production stack |

---

## 📄 License

This project was created as a technical assessment for Blenda Labs.

---

## 🙏 Acknowledgments

- **Blenda Labs** for the interesting technical challenge
- **scikit-learn** for robust ML algorithms
- **MAPIE** for conformal prediction implementation
- **SHAP** for model interpretability
- **FastAPI + React ecosystem** for enabling rapid full-stack development
