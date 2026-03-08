# Environment Best Practices Guide

## Overview

This repository follows industry best practices for managing development and production environments:

- ✅ **Separate environment files** (`.env.development`, `.env.production`)
- ✅ **Environment-specific Docker Compose** (`docker-compose.yml` for dev, `docker-compose.prod.yml` for prod)
- ✅ **Centralized configuration** (`backend/app/settings.py` with Pydantic)
- ✅ **Secrets protection** (`.gitignore` blocks `.env`, `*.key`, credentials)
- ✅ **Example templates** (`.env.example` for team onboarding)

---

## File Structure

```
test_blenda_takehome/
├── .env.example           # Template with all variables (committed)
├── .env.development       # Dev config (committed, no secrets)
├── .env.production        # Prod config template (committed, no secrets)
├── .env.local             # Local overrides (NOT committed, for secrets)
├── docker-compose.yml     # Development stack
├── docker-compose.prod.yml # Production stack (with MLflow, PostgreSQL)
└── backend/app/settings.py # Central configuration class
```

---

## Environment Files Explained

### `.env.example`
- **Purpose**: Documentation and onboarding template
- **Contains**: All available configuration options with descriptions
- **Committed**: ✅ Yes
- **Secrets**: ❌ No

### `.env.development`
- **Purpose**: Development defaults for local work
- **Contains**: `DEBUG=true`, hot-reload enabled, localhost URLs
- **Committed**: ✅ Yes (no secrets - safe to share)
- **Secrets**: ❌ No

### `.env.production`
- **Purpose**: Production configuration template
- **Contains**: Placeholders like `SET_IN_ENV_LOCAL`
- **Committed**: ✅ Yes (template only)
- **Secrets**: ❌ No

### `.env.local` (you create this)
- **Purpose**: **Your actual secrets and local overrides**
- **Contains**: Real passwords, API keys, tokens
- **Committed**: ❌ **NEVER** (blocked by .gitignore)
- **Secrets**: ✅ Yes - **THIS IS WHERE SECRETS GO**

---

## Usage Patterns

### Development Workflow

```bash
# 1. Copy example to create your local file
cp .env.example .env.local

# 2. Edit .env.local with any local customizations (optional)
# nano .env.local

# 3. Start dev stack (uses .env.development by default)
docker compose up

# Environment variables are loaded in this order (later overrides earlier):
# .env.development → .env.local (if exists) → docker-compose.yml environment section
```

### Production Deployment

```bash
# 1. Create production secrets file
cp .env.production .env.local

# 2. Edit .env.local with REAL production secrets
nano .env.local
# Set: POSTGRES_PASSWORD, SECRET_KEY, API keys, etc.

# 3. Start production stack
docker compose -f docker-compose.prod.yml --env-file .env.local up -d

# IMPORTANT: .env.local is NEVER committed to git
```

---

## Configuration Loading Order

```
┌─────────────────────────────────────────┐
│ 1. Backend: settings.py defaults       │
│    (hardcoded fallbacks)                │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ 2. Environment file (.env.development)  │
│    (loaded by Docker Compose)           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ 3. .env.local overrides                 │
│    (secrets and local customizations)   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ 4. docker-compose.yml environment       │
│    (highest priority, inline overrides) │
└─────────────────────────────────────────┘
```

---

## Key Differences: Dev vs Prod

| Configuration | Development | Production |
|---------------|-------------|------------|
| **Debug Mode** | `DEBUG=true` | `DEBUG=false` |
| **Log Level** | `DEBUG` | `INFO` or `WARNING` |
| **API Reload** | `--reload` enabled | Disabled |
| **Workers** | 1 worker | 4+ workers |
| **CORS Origins** | `localhost:*` | Specific domains only |
| **Database** | None (stateless) | PostgreSQL for MLflow |
| **MLflow Tracking** | Disabled | Enabled |
| **Volumes** | Hot-reload mounts | Read-only data mounts |
| **Secrets** | Default/example values | Real credentials in .env.local |

---

## Security Best Practices

### ✅ DO:
- Store secrets in `.env.local` (never committed)
- Use strong passwords in production (generated, not dictionary words)
- Restrict CORS origins in production to your actual domain
- Use `APP_` prefix for application-specific variables
- Rotate credentials regularly
- Use different secrets for dev/staging/prod

### ❌ DON'T:
- Commit `.env.local` or any file with real secrets
- Use default passwords in production (`mlflow/mlflow`)
- Allow `*` CORS origins in production
- Store API keys directly in code or docker-compose.yml
- Reuse production credentials in development

---

## Common Environment Variables

### Application Configuration
```bash
APP_DATA_PATH=/app/sample_videos.csv
APP_CLUSTER_K=2
APP_ANOMALY_CONTAMINATION=0.05
APP_RANDOM_STATE=42
```

### API Settings
```bash
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_RELOAD=false
```

### MLflow (Production)
```bash
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_EXPERIMENT_NAME=content-insights-prod
```

### Database (Production)
```bash
POSTGRES_USER=mlflow
POSTGRES_PASSWORD=<your-secret-password>
POSTGRES_DB=mlflow
POSTGRES_HOST=mlflow-db
POSTGRES_PORT=5432
```

---

## Troubleshooting

### "Environment variable not loaded"
1. Check file exists: `ls -la .env*`
2. Verify Docker Compose references it: `env_file: .env.development`
3. Restart containers: `docker compose down && docker compose up`

### "Secret exposed in git history"
1. Remove from repo: `git rm .env.local`
2. Update .gitignore: `.env.local` should be present
3. Rotate the exposed secret immediately
4. Use `git filter-branch` or BFG Repo-Cleaner to remove history

### "Production using dev config"
1. Ensure you're using: `docker compose -f docker-compose.prod.yml`
2. Pass env file explicitly: `--env-file .env.local`
3. Check settings.py: `settings.environment` should be "production"

---

## Quick Reference

```bash
# Development
docker compose up                              # Uses .env.development
docker compose --env-file .env.local up        # With local overrides

# Production  
docker compose -f docker-compose.prod.yml --env-file .env.local up -d

# Check loaded environment
docker compose config                          # Show resolved config
docker exec backend env | grep APP_            # Show backend env vars

# Create .env.local from template
cp .env.example .env.local
nano .env.local  # Edit with your secrets
```

---

## Next Steps for Production

1. **Set up secrets management**: Use AWS Secrets Manager, HashiCorp Vault, or similar
2. **Add health checks**: Already configured in docker-compose.yml
3. **Set up monitoring**: Sentry for errors, Prometheus for metrics
4. **Configure logging**: Centralized logging with ELK stack or CloudWatch
5. **Implement CI/CD**: Already configured in `.github/workflows/ci.yml`
6. **Set up SSL/TLS**: Use Let's Encrypt with nginx reverse proxy
7. **Database backups**: Automated PostgreSQL backups for MLflow metadata
