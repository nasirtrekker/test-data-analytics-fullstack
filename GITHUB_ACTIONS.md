# GitHub Actions CI/CD Pipeline

Automated testing, building, and deployment workflow for the Content Insights system.

---

## 🎯 Overview

The GitHub Actions pipeline ensures:
- ✅ Code quality checks (linting, type checking)
- ✅ Unit tests pass (pytest with coverage)
- ✅ Conformal coverage validated (> 85%)
- ✅ Docker images built and pushed to registry
- ✅ Deployment to production/staging

---

## 📋 Setup

### 1. Create Secrets in GitHub Repository

Navigate to: Settings → Secrets and variables → Actions

```
DOCKER_REGISTRY_URL = ghcr.io
DOCKER_REGISTRY_USERNAME = [GitHub username]
DOCKER_REGISTRY_TOKEN = [Personal Access Token with write:packages]
```

### 2. Create Workflow Files

Create `.github/workflows/` directory in repository root.

---

## 🔄 Workflow 1: Test on Push

**File**: `.github/workflows/test.yml`

```yaml
name: Test & Lint

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [ "3.11", "3.12" ]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        cd backend
        pip install -e ".[dev]"

    - name: Lint with ruff
      run: |
        cd backend
        ruff check app/ tests/

    - name: Type check with mypy
      run: |
        cd backend
        mypy app/ --ignore-missing-imports

    - name: Run pytest with coverage
      run: |
        cd backend
        pytest tests/ --cov=app --cov-report=xml --cov-report=term
      env:
        APP_DATA_PATH: sample_videos.csv

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./backend/coverage.xml
        flags: backend
        fail_ci_if_error: false

  frontend-test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '20'

    - name: Install dependencies
      run: |
        cd frontend
        npm ci

    - name: Lint
      run: |
        cd frontend
        npm run lint 2>/dev/null || echo "No lint script"

    - name: Build
      run: |
        cd frontend
        npm run build
```

---

## 🏗️ Workflow 2: Build & Push Docker Images

**File**: `.github/workflows/build.yml`

```yaml
name: Build & Push Docker Images

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.DOCKER_REGISTRY_TOKEN }}

    - name: Extract metadata (tags, labels)
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ghcr.io/${{ github.repository }}
        tags: |
          type=ref,event=branch
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha

    - name: Build and push backend
      uses: docker/build-push-action@v4
      with:
        context: ./backend
        push: ${{ github.event_name != 'pull_request' }}
        tags: ghcr.io/${{ github.repository }}/backend:${{ steps.meta.outputs.version }}
        labels: ${{ steps.meta.outputs.labels }}

    - name: Build and push frontend
      uses: docker/build-push-action@v4
      with:
        context: ./frontend
        push: ${{ github.event_name != 'pull_request' }}
        tags: ghcr.io/${{ github.repository }}/frontend:${{ steps.meta.outputs.version }}
        labels: ${{ steps.meta.outputs.labels }}

    - name: Build and push training image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile.training
        push: ${{ github.event_name != 'pull_request' }}
        tags: ghcr.io/${{ github.repository }}/training:${{ steps.meta.outputs.version }}
        labels: ${{ steps.meta.outputs.labels }}
```

---

## 🚀 Workflow 3: Deploy to Production

**File**: `.github/workflows/deploy.yml`

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  workflow_dispatch:  # Manual trigger

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://content-insights.prod.company.com

    steps:
    - uses: actions/checkout@v4

    - name: Deploy to production server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.PROD_SERVER_HOST }}
        username: ${{ secrets.PROD_SERVER_USER }}
        key: ${{ secrets.PROD_SERVER_SSH_KEY }}
        script: |
          cd /opt/content-insights
          git pull origin main
          docker-compose -f docker-compose.prod.yml pull
          docker-compose -f docker-compose.prod.yml up -d
          docker-compose -f docker-compose.prod.yml exec backend pytest tests/

    - name: Run health check
      run: |
        for i in {1..10}; do
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${{ secrets.PROD_SERVER_URL }}/health)
          if [ "$STATUS" = "200" ]; then
            echo "✓ Production health check passed"
            exit 0
          fi
          sleep 5
        done
        echo "✗ Production health check failed"
        exit 1

    - name: Notify deployment
      if: success()
      run: |
        echo "🚀 Deployment successful!"
        # Add Slack/email notification here
```

---

## 📊 Workflow 4: Conformal Coverage Validation

**File**: `.github/workflows/validate-coverage.yml`

```yaml
name: Validate Conformal Coverage

on:
  push:
    branches: [ main, develop ]
  schedule:
    # Run daily at 2 AM UTC (after daily retraining)
    - cron: '0 2 * * *'

jobs:
  check-coverage:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run notebook and check coverage
      run: |
        python -m jupyter execute notebooks/01_exploration_v2.ipynb

        # Extract coverage from notebook output
        COVERAGE=$(grep "coverage=" <(jupyter nbconvert --to script notebooks/01_exploration_v2.ipynb --stdout) | tail -1 | awk -F= '{print $2}')

        MIN_COVERAGE=0.85
        if (( $(echo "$COVERAGE < $MIN_COVERAGE" | bc -l) )); then
          echo "❌ Conformal coverage $COVERAGE is below minimum $MIN_COVERAGE"
          exit 1
        fi
        echo "✓ Conformal coverage $COVERAGE meets minimum requirement"

    - name: Create issue if coverage regressed
      if: failure()
      uses: actions/github-script@v6
      with:
        script: |
          github.rest.issues.create({
            owner: context.repo.owner,
            repo: context.repo.repo,
            title: '⚠️ Conformal coverage regression detected',
            body: 'Coverage fell below 85%. Review predictions and retrain model.',
            labels: ['ml-performance', 'urgent']
          })
```

---

## 📝 Workflow 5: Scheduled Retraining

**File**: `.github/workflows/retrain.yml`

```yaml
name: Scheduled Model Retraining

on:
  schedule:
    # Run weekly on Sunday at 1 AM UTC
    - cron: '0 1 * * 0'
  workflow_dispatch:  # Manual trigger

jobs:
  retrain:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run training notebook
      run: |
        python -m jupyter execute notebooks/01_exploration_v2.ipynb --output notebooks/01_exploration_v2_run.ipynb

    - name: Extract metrics
      run: |
        python << 'EOF'
        import json
        import subprocess

        # Parse notebook output
        result = subprocess.run(['jupyter', 'nbconvert', '--to', 'script',
                                'notebooks/01_exploration_v2.ipynb', '--stdout'],
                               capture_output=True, text=True)

        # Extract key metrics
        output = result.stdout
        r2 = None
        coverage = None

        for line in output.split('\n'):
          if 'R²' in line or 'r2' in line.lower():
            r2 = line
          if 'coverage' in line.lower():
            coverage = line

        print("Training completed!")
        print(f"R²: {r2}")
        print(f"Coverage: {coverage}")
        EOF

    - name: Commit and push updated models
      run: |
        git config --local user.email "ci@company.com"
        git config --local user.name "CI Bot"
        git add models/
        git commit -m "🤖 Automated model retraining ($(date +%Y-%m-%d))" || echo "No changes to commit"
        git push

    - name: Update production with new models
      run: |
        ssh -i ${{ secrets.PROD_SERVER_SSH_KEY }} ${{ secrets.PROD_SERVER_USER }}@${{ secrets.PROD_SERVER_HOST }} \
          "cd /opt/content-insights && docker-compose -f docker-compose.prod.yml restart backend"

    - name: Slack notification
      if: always()
      uses: slackapi/slack-github-action@v1
      with:
        webhook-url: ${{ secrets.SLACK_WEBHOOK }}
        payload: |
          {
            "text": "🔄 Model retraining completed",
            "blocks": [
              {
                "type": "section",
                "text": {
                  "type": "mrkdwn",
                  "text": "*Model Retraining*\nStatus: ${{ job.status }}\nTime: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
                }
              }
            ]
          }
```

---

## 🔍 Configuration: `.github/workflows-config.yml`

```yaml
# Default environment variables used across all workflows

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  PYTHON_VERSION: '3.12'
  NODE_VERSION: '20'
  MIN_COVERAGE: '85'      # Percentage for conformal intervals
  TEST_TIMEOUT: '900'     # 15 minutes
```

---

## ✅ Testing Best Practices

### Pre-commit Checks
```bash
# .git/hooks/pre-commit (run locally before pushing)

#!/bin/bash
cd backend
ruff check app/ tests/ || exit 1
mypy app/ || exit 1
pytest tests/ -x --tb=short || exit 1
cd ../frontend
npm run lint || exit 1
```

### Pull Request Template
```markdown
# Description
Describe the change.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] ML model update

## Testing
- [ ] Tests added
- [ ] Existing tests pass
- [ ] Coverage increased/maintained

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No new warnings generated
```

---

## 📊 Monitoring Workflow Performance

View workflow runs:
```bash
# List all runs
gh run list --repo <owner>/<repo>

# View specific run details
gh run view <run-id> --repo <owner>/<repo>

# Cancel a run
gh run cancel <run-id> --repo <owner>/<repo>
```

---

## 🚨 Status Badges

Add to repository README:

```markdown
![Tests](https://github.com/<owner>/<repo>/actions/workflows/test.yml/badge.svg)
![Build](https://github.com/<owner>/<repo>/actions/workflows/build.yml/badge.svg)
[![codecov](https://codecov.io/gh/<owner>/<repo>/branch/main/graph/badge.svg)](https://codecov.io/gh/<owner>/<repo>)
```

---

## 📚 Troubleshooting

### Workflow Fails on Python Version Mismatch
```yaml
# Use compatible versions
python-version: '3.12'
node-version: '20'
```

### Docker Registry Authentication
```yaml
# Ensure PAT has correct scopes
- write:packages
- read:packages
- delete:packages
```

### Secrets Not Available in Workflow
```yaml
# Check environment and permissions
environment:
  name: production
  # Requires approval for deployment
```

---

## 📖 References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Secrets Management](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
