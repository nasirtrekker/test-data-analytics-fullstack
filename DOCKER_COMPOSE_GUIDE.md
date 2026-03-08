# Docker Compose Configuration Guide

Explains the differences between `docker-compose.yml` and `docker-compose.prod.yml` and when to use each.

---

## 📊 Quick Comparison

| Aspect | Development | Production |
|--------|-------------|------------|
| **File** | `docker-compose.yml` | `docker-compose.prod.yml` |
| **Services** | 2 (Backend + Frontend) | 5 (PostgreSQL + MLflow + Backend + Frontend + Training) |
| **Database** | None | PostgreSQL (persistent) |
| **Model Tracking** | File-based (local) | MLflow (tracked experiments) |
| **Use Case** | Local dev, quick testing | Production, ML monitoring |
| **Startup Time** | ~30 sec | ~2 min (DB init) |
| **Setup Complexity** | Simple | Moderate |
| **Data Persistence** | No | Yes (volumes) |
| **Retraining** | Manual | Automated executor ready |

---

## 🎯 Development: `docker-compose.yml`

### When to Use
- Local development machine
- Quick testing of changes
- No need for model versioning/tracking
- Minimal resources (laptop/dev server)

### Services Included
```yaml
backend:
  - Port: 8000
  - Mounts: sample_videos.csv (read-only)
  - Command: uvicorn with --reload (hot restart on code changes)
  - Database: None (loads from CSV only)

frontend:
  - Port: 5173
  - Command: npm run dev (Vite dev server with HMR)
  - API URL: http://localhost:8000
```

### Quick Start
```bash
docker-compose up --build

# Access:
# - Frontend: http://localhost:5173
# - API: http://localhost:8000/docs
```

### Characteristics
✅ Fast iteration (code changes auto-reload via --reload and npm HMR)
✅ Minimal resource usage
✅ Simple networking (docker-compose handles it)
❌ No experiment tracking
❌ Models lost on container restart
❌ Not production-ready

### File Structure
```yaml
version: '3.9'

services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes:
      - ./sample_videos.csv:/app/sample_videos.csv:ro
    environment:
      - APP_DATA_PATH=/app/sample_videos.csv
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
```

---

## 🏢 Production: `docker-compose.prod.yml`

### When to Use
- Production deployment
- Need experiment tracking & model versioning
- Team collaboration on ML models
- Scheduled retraining jobs
- Multi-environment setup (staging, prod)

### Services Included

#### 1. PostgreSQL (Database)
```yaml
mlflow-db:
  image: postgres:15-alpine
  ports: ["5432:5432"]
  volumes: [mlflow_db_data:/var/lib/postgresql/data]
  healthcheck: Waits for DB to be ready
```
Purpose: Persists MLflow metadata (experiments, runs, parameters)

#### 2. MLflow (Experiment Tracking)
```yaml
mlflow:
  image: python:3.12-slim
  depends_on: mlflow-db
  ports: ["5000:5000"]
  volumes:
    - ./mlruns:/mlruns              # Artifact storage (large files)
    - ./models:/models              # Final models directory
  command: mlflow server --backend-store-uri postgresql://...
  healthcheck: curl http://localhost:5000/
```
Purpose: Web UI for tracking experiments, comparing model versions

#### 3. Backend API
```yaml
backend:
  build: ./backend
  depends_on: mlflow (health check)
  ports: ["8000:8000"]
  environment:
    - MLFLOW_TRACKING_URI=http://mlflow:5000
  volumes:
    - ./sample_videos.csv:/app/sample_videos.csv:ro
    - ./models:/app/models
    - ./mlruns:/app/mlruns
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000
  healthcheck: curl http://localhost:8000/health
```
Purpose: API server with MLflow integration enabled

#### 4. Frontend
```yaml
frontend:
  build: ./frontend
  depends_on: backend (health check)
  ports: ["5173:5173"]
  environment:
    - VITE_API_BASE_URL=http://localhost:8000
  volumes:
    - ./frontend/src:/app/src       # Hot reload during dev
```
Purpose: React dashboard UI

#### 5. Training Pipeline
```yaml
training-pipeline:
  build:
    context: .
    dockerfile: Dockerfile.training
  depends_on: mlflow, backend
  volumes:
    - ./models:/app/models          # Output trained models
    - ./mlruns:/app/mlruns          # Track experiment runs
    - ./notebooks:/app/notebooks
  # No command specified - runs on manual trigger
```
Purpose: On-demand training executor (run `docker-compose exec training-pipeline ...`)

### Startup Sequence
```
1. PostgreSQL starts (5432)
   ↓ Health check passes (pg_isready)

2. MLflow starts (5000)
   ↓ Connects to PostgreSQL
   ↓ Health check passes (curl localhost:5000)

3. Backend starts (8000)
   ↓ Connects to MLflow tracking URI
   ↓ Loads sample_videos.csv
   ↓ Initializes clustering, predictive models
   ↓ Health check passes (curl localhost:8000/health)

4. Frontend starts (5173)
   ↓ Depends on backend ready
   ↓ Starts Vite dev server

5. Training Pipeline (idle)
   ↓ Ready for manual execution or cron scheduling
```

Estimated total startup: 90-120 seconds

### Quick Start
```bash
docker-compose -f docker-compose.prod.yml up --build

# Access in separate terminals:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000/docs
# - MLflow UI: http://localhost:5000
```

### Persistence
✅ Database: PostgreSQL keeps metadata across restarts
✅ Artifacts: Named volume `mlruns_db_data` stores MLflow runs
✅ Models: Host mount `./models` persists trained models
✅ Reproducibility: MLflow tracks exact parameters/code versions

### Characteristics
✅ Production-ready networking and health checks
✅ Persistent data storage (PostgreSQL + volumes)
✅ Experiment tracking and versioning (MLflow)
✅ Automated retraining support
✅ Multi-environment ready
❌ Slightly more resource-intensive
❌ Requires PostgreSQL knowledge for troubleshooting
❌ Slower startup (~2 min vs 30 sec)

---

## 🔄 Migration: Dev → Prod

### Step 1: Develop Locally (Dev Config)
```bash
# Use docker-compose.yml for quick iteration
docker-compose up

# Make changes, test API/UI
# Models saved locally if needed
```

### Step 2: Test Production Config Locally
```bash
# Switch to prod compose file
docker-compose -f docker-compose.prod.yml up --build

# Verify:
# - MLflow UI shows experiments
# - Backend still works
# - Frontend still works
# - Health checks passing
```

### Step 3: Deploy to Production Server
```bash
# On prod server:
git clone <repo>
cd test_blenda_takehome

# Create .env file for secrets (don't commit to git!)
cat > .env <<EOF
POSTGRES_PASSWORD=secure-random-password-here
MLFLOW_TRACKING_URL=https://mlflow.yourcompany.com
EOF

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify
docker-compose -f docker-compose.prod.yml logs
docker-compose -f docker-compose.prod.yml ps
```

---

## 📋 Configuration Comparison

### Environment Variables

**Development (`docker-compose.yml`)**
```yaml
environment:
  - APP_DATA_PATH=/app/sample_videos.csv
```

**Production (`docker-compose.prod.yml`)**
```yaml
Backend:
  environment:
    - MLFLOW_TRACKING_URI=http://mlflow:5000
    - PYTHONUNBUFFERED=1

MLflow:
  environment:
    - POSTGRES_USER=mlflow
    - POSTGRES_PASSWORD=mlflow
    - POSTGRES_DB=mlflow
```

### Volume Mounts

**Development**
```yaml
volumes:
  - ./sample_videos.csv:/app/sample_videos.csv:ro  # Read-only
```

**Production**
```yaml
volumes:
  - ./sample_videos.csv:/app/sample_videos.csv:ro
  - ./models:/app/models                       # Full model directory
  - ./mlruns:/app/mlruns                       # MLflow artifacts
  - mlflow_db_data:/var/lib/postgresql/data   # Named volume for DB
```

### Health Checks

**Development**: None specified (not critical)

**Production**: All services have health checks
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 10s
  timeout: 5s
  retries: 5
```

---

## 🎬 Common Workflows

### Workflow 1: Quick Local Testing
```bash
# 1. Make code changes
# 2. Run dev compose
docker-compose up --build

# 3. Test in browser: http://localhost:5173
# Changes auto-reload via --reload flag

# 4. When done
docker-compose down
```

### Workflow 2: Add New ML Feature
```bash
# 1. Update notebook
vim notebooks/01_exploration_v2.ipynb

# 2. Run notebook to generate new models
jupyter lab  # Run all cells

# 3. Update backend code if needed
vim backend/app/analysis_*.py

# 4. Test locally with dev compose
docker-compose up --build

# 5. Commit and push
git add .
git commit -m "Add feature X"
git push

# 6. CI/CD builds and pushes to registry
# 7. Production pulls latest image
```

### Workflow 3: Retrain Models in Production
```bash
# On production server:
docker-compose -f docker-compose.prod.yml exec training-pipeline \
  python -m jupyter execute notebooks/01_exploration_v2.ipynb

# Or manually trigger via cron:
# 0 2 * * * cd /path/to/app && docker-compose -f docker-compose.prod.yml \
#   exec training-pipeline python -m jupyter execute notebooks/01_exploration_v2.ipynb
```

### Workflow 4: Debug Production Issue
```bash
# Check service logs
docker-compose -f docker-compose.prod.yml logs backend -f

# Enter container for investigation
docker-compose -f docker-compose.prod.yml exec backend bash
  # Inside: ls /app/models
  # Inside: curl http://mlflow:5000/health
  # Inside: python -c "from app.etl import load_clean; df = load_clean('/app/sample_videos.csv')"

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# View resource usage
docker stats
```

---

## 🔐 Security Considerations

### Development (Less Critical)
- Local only, no auth needed
- Volumes with full permissions
- No secrets management

### Production (Critical)

#### Use .env File for Secrets
```bash
# .env (never commit to git!)
POSTGRES_PASSWORD=generate-random-password-here
POSTGRES_USER=mlflow_user
SECRET_KEY=another-random-secret

# In docker-compose
environment:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

#### Environment-Specific Config
```bash
# .env.prod
MLFLOW_TRACKING_URI=https://secure-mlflow-server.com

# docker-compose.prod.yml overrides
env_file:
  - .env.prod
```

#### Network Isolation
```yaml
networks:
  internal:
    internal: true  # Containers only, no external access
  frontend:        # For external access (load balancer)
```

---

## 📊 Scaling Considerations

### Horizontal Scaling (Multiple Backend Instances)

**Current setup**: 1 backend, 1 frontend

**To scale**:
```yaml
backend:
  deploy:
    replicas: 3      # Run 3 instances of backend

# Add load balancer (nginx)
nginx:
  image: nginx:alpine
  ports: ["80:80"]
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
  depends_on:
    - backend
```

### Vertical Scaling (More Resources)

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## 🐛 Troubleshooting

### Can't Connect to Backend from Frontend
**Dev issue**: VITE_API_URL points to wrong host
**Solution**: Verify in `frontend/vite.config.ts` or `.env`

**Prod issue**: Services on different networks
**Solution**: Ensure both on same docker network or use service names (http://backend:8000)

### PostgreSQL Won't Start (Prod)
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs mlflow-db

# Common causes:
# - Port 5432 already in use
# - Volume permission issues
# - Insufficient disk space

# Fix: Clean volumes and restart
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d
```

### MLflow Experiments Not Showing
```bash
# Verify backend connected to MLflow
docker exec <backend-container> env | grep MLFLOW

# Check MLflow is running
docker-compose -f docker-compose.prod.yml ps | grep mlflow

# Manually check connection
docker exec backend python -c "import mlflow; print(mlflow.get_tracking_uri())"
```

---

## 📖 References

- [Docker Compose v3 Reference](https://docs.docker.com/compose/compose-file/compose-file-v3/)
- [MLflow Docker Setup](https://mlflow.org/docs/latest/deployments/index.html)
- [Health Checks Documentation](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Named Volumes Best Practices](https://docs.docker.com/storage/volumes/)
