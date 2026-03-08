# Docker & Deployment Guide

Complete instructions for building, running, and deploying the Content Insights system using Docker and Docker Compose.

---

## 🎯 Quick Reference

| Scenario | Command | Use Case |
|----------|---------|----------|
| **Dev (5 min setup)** | `docker-compose up --build` | Local development, testing |
| **Prod (full stack)** | `docker-compose -f docker-compose.prod.yml up --build` | Production with MLflow tracking |
| **Build backend only** | `docker build -t insights:backend ./backend` | CI/CD pipeline |
| **Build frontend only** | `docker build -t insights:frontend ./frontend` | UI updates |
| **Build training** | `docker build -f Dockerfile.training -t insights:training .` | Scheduled retraining |
| **Clean everything** | `docker-compose down -v && docker system prune -a` | Fresh start |

---

## 📋 Prerequisites

```bash
# Check installations
docker --version        # Docker 20.10+
docker-compose --version  # Docker Compose 2.0+
# or: docker compose version (newer syntax)

# If not installed:
# macOS: brew install docker docker-compose
# Linux: sudo apt-get install docker.io docker-compose
# Windows: Download Docker Desktop
```

---

## 🚀 Option 1: Development Setup (Lightweight)

### Files Used
- `docker-compose.yml` - Backend + Frontend only
- `backend/Dockerfile` - Minimal Python image, ~400MB
- `frontend/Dockerfile` - Node Alpine image, ~100MB

### Step-by-Step

```bash
# 1. From project root
cd test_blenda_takehome

# 2. Build and run (backend + frontend)
docker-compose up --build

# First run takes ~2-3 min (downloads Python/Node base images, installs deps)
# Subsequent runs: ~30 sec

# Expected output:
# backend     | Uvicorn running on http://0.0.0.0:8000
# frontend    | Local: http://localhost:5173

# 3. In new terminal, verify
curl http://localhost:8000/health       # Backend
curl http://localhost:8000/docs         # Swagger UI
# Open http://localhost:5173 in browser
```

### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs            # All services
```

### Stop & Cleanup
```bash
docker-compose down            # Stop containers, keep volumes
docker-compose down -v         # Stop + remove volumes (data loss!)
docker-compose restart         # Restart without rebuilding
```

---

## 🔧 Option 2: Production Setup (Full ML Stack)

### Files Used
- `docker-compose.prod.yml` - 5 services:
  1. **PostgreSQL** - MLflow database
  2. **MLflow** - Model registry & experiment tracking
  3. **Backend** - FastAPI content-insights service
  4. **Frontend** - React dashboard
  5. **Training Pipeline** - Jupyter-based retraining executor

### Advantages
- ✅ Model versioning and experiment tracking (MLflow)
- ✅ Reproducible training in containers
- ✅ Database persistence across restarts
- ✅ Health checks for all services
- ✅ Production-ready networking

### Step-by-Step

```bash
# 1. Build all services
docker-compose -f docker-compose.prod.yml build

# 2. Start all services
docker-compose -f docker-compose.prod.yml up

# Expected startup order (with health checks):
# PostgreSQL starts (5432)
#   ↓ postgres ready
# MLflow starts (5000)
#   ↓ mlflow ready
# Backend starts (8000 - depends on mlflow)
#   ↓ backend ready
# Frontend starts (5173 - depends on backend)
# Training Pipeline (on-demand executor)

# 3. Verify all services
docker-compose -f docker-compose.prod.yml ps

# Status check example:
# NAME                   STATUS              PORTS
# mlflow-database        Up 45s (healthy)    0.0.0.0:5432->5432/tcp
# mlflow-tracking        Up 30s (healthy)    0.0.0.0:5000->5000/tcp
# content-insights-api   Up 20s (healthy)    0.0.0.0:8000->8000/tcp
# content-insights-ui    Up 10s (healthy)    0.0.0.0:5173->5173/tcp
```

### Access Services

```bash
# Frontend dashboard
open http://localhost:5173

# API documentation
open http://localhost:8000/docs

# MLflow experiment tracking
open http://localhost:5000
# Click "Experiments" to see model runs

# PostgreSQL (if needed)
psql -h localhost -U mlflow -d mlflow
# Password: mlflow
```

### Stop Production Stack
```bash
docker-compose -f docker-compose.prod.yml down        # Keeps data
docker-compose -f docker-compose.prod.yml down -v     # Deletes database
docker-compose -f docker-compose.prod.yml logs backend # View logs
```

---

## 🏗️ Option 3: Build Individual Services

### Backend Only

```bash
# Build
docker build -t content-insights-backend:latest ./backend

# Run with volume mount (hot reload)
docker run -d \
  --name backend \
  -p 8000:8000 \
  -v $(pwd)/sample_videos.csv:/app/sample_videos.csv:ro \
  -e APP_DATA_PATH=/app/sample_videos.csv \
  content-insights-backend:latest

# Verify
curl http://localhost:8000/health

# View logs
docker logs -f backend

# Stop
docker stop backend && docker rm backend
```

### Frontend Only

```bash
# Build
docker build -t content-insights-frontend:latest ./frontend

# Run
docker run -d \
  --name frontend \
  -p 5173:5173 \
  -e VITE_API_BASE_URL=http://localhost:8000 \
  content-insights-frontend:latest

# Access: http://localhost:5173
docker logs -f frontend
docker stop frontend && docker rm frontend
```

### Backend + Frontend (Manual Coordination)

```bash
# Terminal 1: Backend
docker build -t insights-backend ./backend
docker run -d \
  --name insights-backend \
  -p 8000:8000 \
  -v $(pwd)/sample_videos.csv:/app/sample_videos.csv:ro \
  insights-backend

# Terminal 2: Frontend
docker build -t insights-frontend ./frontend
docker run -d \
  --name insights-frontend \
  -p 5173:5173 \
  -e VITE_API_BASE_URL=http://localhost:8000 \
  insights-frontend

# Check both running
docker ps | grep insights

# Cleanup
docker stop insights-backend insights-frontend
docker rm insights-backend insights-frontend
```

---

## 🎓 Training Pipeline (Model Retraining)

The `Dockerfile.training` enables containerized ML training.

### Single Training Run

```bash
# Build training image
docker build -f Dockerfile.training -t insights-training:latest .

# Run training (generates new models)
docker run --rm \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/sample_videos.csv:/app/sample_videos.csv:ro \
  -e APP_DATA_PATH=/app/sample_videos.csv \
  insights-training:latest

# Models saved to local ./models/ directory
ls -la models/
# clusters_v2.joblib
# predictive_mapie.joblib
# manifest.json
# etc.
```

### Production Retraining Cron Job

```bash
# Script: scripts/daily_retrain.sh
#!/bin/bash
cd /path/to/test_blenda_takehome
DATE=$(date +%Y%m%d)
docker run --rm \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/mlruns:/app/mlruns \
  -v $(pwd)/sample_videos.csv:/app/sample_videos.csv:ro \
  insights-training:latest

# Add to crontab: 0 2 * * * /path/to/scripts/daily_retrain.sh
```

### Scheduled Training in docker-compose.prod.yml

```bash
# The training-pipeline service runs on-demand
# To execute:
docker-compose -f docker-compose.prod.yml exec training-pipeline \
  python -m jupyter execute notebooks/01_exploration_v2.ipynb
```

---

## 📦 Docker Image Details

### `backend/Dockerfile`
```dockerfile
FROM python:3.12-slim
# Use minimal Python image (~150MB base)
# Install dependencies from pyproject.toml
# Expose port 8000
# Default command: uvicorn app.main:app --host 0.0.0.0 --port 8000
```
**Image size**: ~400-500MB
**Startup time**: 5-10 sec
**Production ready**: ✅ Yes

### `frontend/Dockerfile`
```dockerfile
FROM node:20-alpine
# Use Alpine Node (very small, ~40MB base)
# Install npm dependencies
# Build React app for production
# Expose port 5173
# Run: npm run dev
```
**Image size**: ~200-300MB
**Startup time**: 3-5 sec
**Production ready**: ✅ Yes (for dev), ⚠️ Run `npm run build && npm run serve` for prod

### `Dockerfile.training` (Multi-stage)
```dockerfile
# Stage 1: Builder
FROM python:3.12-slim as builder
# Install build tools, compile dependencies
# (wheels for scipy, scikit-learn, etc.)

# Stage 2: Runtime
FROM python:3.12-slim
# Copy only compiled packages from builder
# Add notebooks, scripts, sample data
# Entrypoint: jupyter execute
```
**Image size**: ~800MB (includes jupyter, all ML libs)
**Startup time**: 15-30 sec
**Use case**: Scheduled retraining, not production API

---

## 🚀 Advanced Deployment Scenarios

### Docker Network Setup (Manual Services)

```bash
# Create network
docker network create insights-net

# Run backend on network
docker run -d \
  --name backend \
  --network insights-net \
  -p 8000:8000 \
  content-insights-backend

# Run frontend on same network
# Frontend can reach backend at http://backend:8000
docker run -d \
  --name frontend \
  --network insights-net \
  -p 5173:5173 \
  -e VITE_API_BASE_URL=http://backend:8000 \
  content-insights-frontend

# Cleanup
docker network rm insights-net
```

### Push to Docker Registry

```bash
# Tag for Docker Hub
docker tag content-insights-backend:latest \
  myusername/content-insights-backend:latest

# Push
docker push myusername/content-insights-backend:latest

# Or use GitHub Container Registry
docker tag content-insights-backend:latest \
  ghcr.io/myorg/content-insights-backend:latest
docker push ghcr.io/myorg/content-insights-backend:latest
```

### ARM64 Support (M1/M2 Mac, Raspberry Pi)

```bash
# Build for ARM64
docker buildx build --platform linux/arm64 \
  -t content-insights-backend:arm64 \
  ./backend

# Build multi-platform (requires buildx)
docker buildx build --platform linux/amd64,linux/arm64 \
  -t content-insights-backend:multi \
  ./backend
```

---

## 🔍 Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
docker run -p 9000:8000 content-insights-backend
```

### Containers Keep Crashing

```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Missing environment variables (APP_DATA_PATH, VITE_API_BASE_URL)
# - Volume mount paths incorrect
# - sample_videos.csv not found

# Debug by running interactively
docker run -it backend /bin/bash
# Inside container: ls /app, echo $APP_DATA_PATH, etc.
```

### Network Issues Between Services

```bash
# Ensure services on same network
docker network inspect insights-net  # if custom network

# Test connectivity from container
docker exec backend curl http://localhost:8000/health

# Check DNS resolution
docker exec frontend nslookup backend
```

### Database Connection Errors (Production)

```bash
# Verify PostgreSQL running
docker-compose -f docker-compose.prod.yml logs mlflow-db

# Test connection from MLflow container
docker exec mlflow-tracking \
  psql -h mlflow-db -U mlflow -d mlflow -c "SELECT 1"
```

### Volume Mount Permission Denied

```bash
# Linux: Docker runs as root, may not have read/write to host volumes
# Solution 1: Run with user ID
docker run -u $(id -u):$(id -g) ...

# Solution 2: Change file permissions
chmod 666 sample_videos.csv

# Solution 3: Use :ro (read-only) if possible
-v $(pwd)/sample_videos.csv:/app/sample_videos.csv:ro
```

---

## 📊 Performance Tips

### Reduce Build Time

```bash
# Use .dockerignore to exclude unnecessary files
echo "node_modules
__pycache__
.git
.pytest_cache
models/
mlruns/" > .dockerignore

# Build without cache if needed
docker-compose build --no-cache
```

### Runtime Optimization

```bash
# Use multi-stage builds (training Dockerfile already does this)
# Result: ~200MB smaller final image

# Limit container memory
docker run -m 2g content-insights-backend

# Use alpine-based images where possible
# backend: python:3.12-slim (150MB)
# frontend: node:20-alpine (40MB)
```

---

## 📚 Reference Commands

```bash
# List all images
docker images | grep insights

# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Show image layers and size
docker history content-insights-backend

# Execute command in running container
docker exec backend python -m pytest tests/

# Copy file from container
docker cp backend:/app/models ./local_models

# Docker cleanup
docker system prune           # Remove unused images/networks
docker system prune -a        # Remove all unused
docker volume prune           # Remove unused volumes
```

---

## 🎯 Production Deployment Checklist

- [ ] Sensitive data: Store in `.env` file, not in Dockerfiles
- [ ] Health checks: Verify all services have `healthcheck` directive
- [ ] Volumes: Use named volumes for data persistence, not bind mounts
- [ ] Logging: Configure logging drivers (splunk, datadog, etc.)
- [ ] Networking: Use internal networks, expose only necessary ports
- [ ] Resource limits: Set memory/CPU limits per service
- [ ] Restart policies: Use `restart: always` for production
- [ ] Security: Scan images with Trivy, use minimal base images
- [ ] Automation: Set up CI/CD to build and push on git push
- [ ] Monitoring: Wire up Prometheus, Grafana, or cloud provider monitoring

---

## 📖 Further Reading

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Compose Docs](https://docs.docker.com/compose/compose-file/)
- [Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Security](https://docs.docker.com/engine/security/)
