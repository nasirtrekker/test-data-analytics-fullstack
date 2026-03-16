# Documentation Index

This directory contains comprehensive guides and references for the Blenda Test Data Analytics Full Stack Solution.

## 📋 Quick Navigation

### For New Users

1. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Start here for project overview
2. **[ENVIRONMENT_BEST_PRACTICES.md](ENVIRONMENT_BEST_PRACTICES.md)** - Setup your environment
3. **[DOCKER_GUIDE.md](DOCKER_GUIDE.md)** - Learn Docker basics for this project

### For Developers

- **[PYTEST_TESTING.md](PYTEST_TESTING.md)** - Writing and running tests
- **[DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md)** - Local development with Docker
- **[PUSH_CHECKLIST.md](PUSH_CHECKLIST.md)** - Pre-commit checklist

### For DevOps/Deployment

- **[GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)** - CI/CD pipeline configuration
- **[MONITORING.md](MONITORING.md)** - Application monitoring and health checks
- **[PUSH_TO_GITHUB.md](PUSH_TO_GITHUB.md)** - Git workflow and deployment

---

## 📚 All Documentation Files

| File | Purpose | Audience |
|------|---------|----------|
| [**ENVIRONMENT_BEST_PRACTICES.md**](ENVIRONMENT_BEST_PRACTICES.md) | `.env` file management, configuration best practices | All developers |
| [**GITHUB_ACTIONS.md**](GITHUB_ACTIONS.md) | CI/CD pipeline documentation | DevOps, maintainers |
| [**MONITORING.md**](MONITORING.md) | Health checks, logging, performance metrics | DevOps, SRE |
| [**DOCKER_COMPOSE_GUIDE.md**](DOCKER_COMPOSE_GUIDE.md) | Multi-container orchestration | Developers |
| [**DOCKER_GUIDE.md**](DOCKER_GUIDE.md) | Containerization fundamentals | New developers |
| [**PYTEST_TESTING.md**](PYTEST_TESTING.md) | Test framework, coverage, writing tests | Developers |
| [**PUSH_TO_GITHUB.md**](PUSH_TO_GITHUB.md) | Git workflow, commit conventions | All contributors |
| [**PUSH_CHECKLIST.md**](PUSH_CHECKLIST.md) | Quick pre-push validation steps | All contributors |
| [**PROJECT_SUMMARY.md**](PROJECT_SUMMARY.md) | Architecture, tech stack, decisions | New team members |

---

## 🖼️ Screenshots

Live dashboard captures from the current build:

<table>
	<tr>
		<td width="50%">
			<img src="../screenshots/dashboard_up_clustering.png" alt="Clustering dashboard" width="100%" />
			<p><strong>Clustering Dashboard</strong><br/>Content tier segmentation and visual grouping.</p>
		</td>
		<td width="50%">
			<img src="../screenshots/dashboard_anomaliy.png" alt="Anomaly dashboard" width="100%" />
			<p><strong>Anomaly Dashboard</strong><br/>Outlier identification for investigation.</p>
		</td>
	</tr>
	<tr>
		<td width="50%">
			<img src="../screenshots/dashboard_predictivemodel.png" alt="Predictive model benchmark" width="100%" />
			<p><strong>Predictive Benchmark</strong><br/>Model vs naive baseline with acceptance decision.</p>
		</td>
		<td width="50%">
			<img src="../screenshots/dashboard_modelmetricst_forecastabilty.png" alt="Forecastability metrics dashboard" width="100%" />
			<p><strong>Model Metrics and Forecastability</strong><br/>Uncertainty metrics and coverage diagnostics.</p>
		</td>
	</tr>
	<tr>
		<td width="50%">
			<img src="../screenshots/dashboard_mlflow.png" alt="MLflow experiments" width="100%" />
			<p><strong>MLflow Tracking</strong><br/>Runs, artifacts, and reproducibility metadata.</p>
		</td>
		<td width="50%">
			<img src="../screenshots/dashboard_api.png" alt="API docs" width="100%" />
			<p><strong>FastAPI Docs</strong><br/>Interactive endpoint contracts and payload examples.</p>
		</td>
	</tr>
</table>

---

## 🔍 Find Documentation by Topic

### Environment Configuration
- Setting up dev/prod environments → [ENVIRONMENT_BEST_PRACTICES.md](ENVIRONMENT_BEST_PRACTICES.md)
- Docker environment variables → [DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md)

### Testing & Quality
- Running tests locally → [PYTEST_TESTING.md](PYTEST_TESTING.md)
- Pre-push validation → [PUSH_CHECKLIST.md](PUSH_CHECKLIST.md)
- CI/CD automated tests → [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)

### Deployment & Operations
- Docker containerization → [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
- Multi-service setup → [DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md)
- Monitoring & health → [MONITORING.md](MONITORING.md)
- Git workflow → [PUSH_TO_GITHUB.md](PUSH_TO_GITHUB.md)

### Architecture & Design
- System architecture → [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- Technology choices → [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

---

## 🚀 Common Documentation Workflows

### I'm new to this project
1. Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for overview
2. Follow [ENVIRONMENT_BEST_PRACTICES.md](ENVIRONMENT_BEST_PRACTICES.md) to set up
3. Reference [DOCKER_GUIDE.md](DOCKER_GUIDE.md) or [DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md) for containers

### I want to contribute code
1. Check [PUSH_CHECKLIST.md](PUSH_CHECKLIST.md) for requirements
2. Run tests per [PYTEST_TESTING.md](PYTEST_TESTING.md)
3. Follow [PUSH_TO_GITHUB.md](PUSH_TO_GITHUB.md) workflow

### I need to deploy/maintain the app
1. Review [DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md) for deployment
2. Set up [MONITORING.md](MONITORING.md) for health checks
3. Configure [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) for CI/CD

### I'm troubleshooting an issue
1. Check [MONITORING.md](MONITORING.md) for logs and metrics
2. Review [DOCKER_COMPOSE_GUIDE.md](DOCKER_COMPOSE_GUIDE.md) for container issues
3. See [PYTEST_TESTING.md](PYTEST_TESTING.md) for test failures

---

## 📝 Contributing to Documentation

When adding or updating documentation:
1. Keep files focused on a single topic
2. Use clear headings and code examples
3. Update this index (README.md) with new files
4. Cross-reference related documentation
5. Include command examples with expected outputs

---

**[← Back to Main README](../README.md)**
