# Monitoring & Observability Guide

> **⚠️ ROADMAP DOCUMENTATION**: This document describes future production monitoring capabilities (Prometheus, Grafana, alerting). These services are not currently configured in docker-compose files. This serves as a reference architecture for production deployment.

Comprehensive monitoring strategy for production deployments, ML model performance, and system health.

---

## 🎯 Monitoring Objectives

- ✅ **System Health**: API uptime, response times, error rates
- ✅ **Model Performance**: Conformal coverage drift, prediction accuracy degradation
- ✅ **Data Quality**: Input feature distributions, anomalies
- ✅ **Business Metrics**: Prediction usage, user engagement
- ✅ **Infrastructure**: Resource usage, container health, database performance

---

## 📊 Metrics to Track

### API & System Metrics

| Metric | Threshold | Alert | Tool |
|--------|-----------|-------|------|
| Response time (p95) | < 500ms | > 1s | Prometheus |
| Error rate | < 1% | > 5% | Prometheus |
| Health check status | 200 | 5xx | Pinger |
| Uptime | > 99.9% | < 99% | Uptime Robot |
| CPU usage | < 80% | > 90% | Prometheus |
| Memory usage | < 85% | > 95% | Prometheus |
| DB connection pool | < 80% | > 90% | Prometheus |

### ML Model Metrics

| Metric | Baseline | Alert | Frequency |
|--------|----------|-------|-----------|
| Conformal coverage | 90% ± 5% | < 85% or > 98% | Daily |
| Prediction MAE | 0.001 (baseline) | +50% increase | Daily |
| SHAP feature stability | Same rank order | Top 5 changed | Weekly |
| Data drift (KS test) | p > 0.05 | p < 0.05 | Daily |
| Model latency | < 100ms | > 500ms | Hourly |
| Calibration curve | Well-calibrated | Off-diagonal | Weekly |

---

## 🔧 Implementation

### 1. Application Metrics (Prometheus)

**Install dependencies:**
```bash
pip install prometheus-client
```

**Add instrumentation to backend/app/main.py:**
```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
request_count = Counter(
    'insights_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'insights_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

active_models = Gauge(
    'insights_active_models',
    'Number of active ML models'
)

conformal_coverage = Gauge(
    'insights_conformal_coverage',
    'Conformal prediction coverage'
)

@app.middleware("http")
async def track_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)

    duration = time.time() - start_time
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response

@app.get("/metrics-endpoint")
def export_metrics():
    """Prometheus metrics endpoint."""
    from prometheus_client import generate_latest
    return generate_latest()
```

---

### 2. ML Model Monitoring

**Add monitoring to backend/app/monitoring.py (new file):**

```python
import pandas as pd
import numpy as np
from scipy import stats
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ModelMetricsSnapshot:
    timestamp: datetime
    conformal_coverage: float
    prediction_mae: float
    prediction_rmse: float
    feature_stability_score: float
    data_drift_detected: bool
    average_inference_time: float
    sample_size: int

class ModelMonitor:
    def __init__(self, baseline_metrics: dict):
        """Initialize with baseline metrics from training."""
        self.baseline = baseline_metrics
        self.history = []

    def check_conformal_coverage(self, actual, predicted_low, predicted_high):
        """Calculate conformal interval coverage."""
        coverage = np.mean(
            (actual >= predicted_low) & (actual <= predicted_high)
        )

        min_coverage = 0.85
        max_coverage = 0.98

        if coverage < min_coverage:
            raise AlertException(f"Coverage {coverage:.2%} below minimum {min_coverage:.2%}")
        if coverage > max_coverage:
            raise AlertException(f"Coverage {coverage:.2%} exceeds maximum {max_coverage:.2%}")

        return coverage

    def check_feature_drift(self, current_df, baseline_df, features):
        """Detect data drift using Kolmogorov-Smirnov test."""
        drift_detected = False
        p_values = {}

        for feature in features:
            # KS test: null hypothesis is same distribution
            stat, p_value = stats.ks_2samp(
                baseline_df[feature].fillna(0),
                current_df[feature].fillna(0)
            )
            p_values[feature] = p_value

            if p_value < 0.05:  # Significant difference
                drift_detected = True

        return drift_detected, p_values

    def check_prediction_accuracy(self, actual, predicted):
        """Monitor prediction accuracy degradation."""
        mae = np.mean(np.abs(actual - predicted))
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))

        baseline_mae = self.baseline.get('mae', 0.001)

        if mae > baseline_mae * 1.5:  # 50% worse than baseline
            raise AlertException(
                f"MAE {mae:.6f} degraded vs baseline {baseline_mae:.6f}"
            )

        return mae, rmse

    def create_snapshot(self, df, predictions, actual):
        """Create a monitoring snapshot."""
        coverage = self.check_conformal_coverage(
            actual,
            predictions['pi_low'],
            predictions['pi_high']
        )

        mae, rmse = self.check_prediction_accuracy(actual, predictions['pred'])

        # Feature stability (check if top features remain in order)
        feature_stability = 0.95  # Placeholder

        return ModelMetricsSnapshot(
            timestamp=datetime.now(),
            conformal_coverage=coverage,
            prediction_mae=mae,
            prediction_rmse=rmse,
            feature_stability_score=feature_stability,
            data_drift_detected=False,
            average_inference_time=0.05,
            sample_size=len(df)
        )

class AlertException(Exception):
    """Raised when monitoring thresholds are exceeded."""
    pass
```

---

### 3. Logging Configuration

**backend/app/logger.py:**

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging."""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
        }

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def setup_logging():
    """Configure application logging."""
    logger = logging.getLogger("content-insights")
    logger.setLevel(logging.INFO)

    # Console handler with JSON formatting
    handler = logging.StreamHandler()
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# Usage in application
logger = setup_logging()
logger.info("API started", extra={'version': '2.0.0'})
```

---

### 4. Health Check Endpoint

**backend/app/main.py - Enhanced:**

```python
from .monitoring import ModelMonitor

@app.get("/health/deep")
def deep_health_check(state: State = Depends(get_state)):
    """Comprehensive health check including ML model state."""

    checks = {
        'api': 'healthy',
        'database': 'healthy',
        'models': {},
        'timestamp': datetime.now().isoformat()
    }

    try:
        # Check model artifacts exist
        if hasattr(state, 'predictive'):
            checks['models']['predictive'] = {
                'status': 'loaded',
                'coverage': state.predictive.metrics.get('coverage'),
                'mae': state.predictive.metrics.get('mae')
            }

        # Check data freshness
        if hasattr(state, 'df'):
            max_date = state.df['publish_date'].max()
            days_old = (datetime.now() - max_date).days
            checks['data_age_days'] = days_old

            if days_old > 30:
                checks['data'] = 'stale'
            else:
                checks['data'] = 'fresh'

    except Exception as e:
        checks['error'] = str(e)
        return {'status': 'unhealthy', **checks}, 503

    return checks
```

---

## 📈 Monitoring Dashboards

### Grafana Dashboard Setup

**1. Add Prometheus data source:**
- URL: `http://prometheus:9090`

**2. Key dashboard panels:**

```json
{
  "dashboard": {
    "title": "Content Insights Monitoring",
    "panels": [
      {
        "title": "API Response Time (p95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, insights_api_request_duration_seconds_bucket)"
        }]
      },
      {
        "title": "Conformal Coverage",
        "targets": [{
          "expr": "insights_conformal_coverage"
        }]
      },
      {
        "title": "Error Rate (%)",
        "targets": [{
          "expr": "100 * rate(insights_api_requests_total{status=~'5..'}[5m])"
        }]
      },
      {
        "title": "Prediction MAE",
        "targets": [{
          "expr": "insights_model_mae"
        }]
      }
    ]
  }
}
```

---

## 🚨 Alerting Strategy

### Prometheus Alert Rules (`alert-rules.yml`)

```yaml
groups:
- name: content_insights_alerts
  rules:

  - alert: HighErrorRate
    expr: rate(insights_api_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High error rate detected"
      severity: "critical"

  - alert: ConformalCoverageLow
    expr: insights_conformal_coverage < 0.85
    for: 1h
    annotations:
      summary: "Conformal coverage below 85% - model drift likely"
      severity: "warning"

  - alert: ResponseTimeHigh
    expr: histogram_quantile(0.95, insights_api_request_duration_seconds_bucket) > 1.0
    for: 10m
    annotations:
      summary: "API response time degradation"
      severity: "warning"

  - alert: DataDriftDetected
    expr: insights_data_drift_detected == 1
    for: 0m
    annotations:
      summary: "Data distribution has changed significantly"
      severity: "warning"

  - alert: ModelInferenceTimeHigh
    expr: insights_model_inference_time_seconds > 0.5
    for: 5m
    annotations:
      summary: "Model inference time exceeds threshold"
      severity: "warning"
```

Configure Alertmanager to send to Slack/PagerDuty/Email.

---

## 📊 Daily Monitoring Report

**Script: scripts/monitoring_report.py**

```python
#!/usr/bin/env python
"""Generate daily monitoring report."""

import requests
import json
from datetime import datetime, timedelta

def generate_report():
    """Create daily monitoring summary."""

    # Fetch metrics
    api_health = requests.get("http://localhost:8000/health/deep").json()
    metrics = requests.get("http://localhost:8000/metrics-endpoint").text

    # Parse predictions from last 24h
    yesterday = datetime.now() - timedelta(days=1)

    report = f"""
    📊 Content Insights Monitoring Report
    Generated: {datetime.now().isoformat()}

    ## System Health
    - API Status: {api_health.get('api')}
    - Database: {api_health.get('database')}
    - Data Age: {api_health.get('data_age_days')} days

    ## ML Model Performance
    - Conformal Coverage: {api_health['models'].get('predictive', {}).get('coverage', 'N/A')}
    - Prediction MAE: {api_health['models'].get('predictive', {}).get('mae', 'N/A')}
    - Status: {api_health['models'].get('predictive', {}).get('status')}

    ## Alerts (Last 24h)
    {get_recent_alerts()}

    ## Recommendations
    {get_recommendations(api_health)}
    """

    return report

if __name__ == "__main__":
    report = generate_report()
    print(report)

    # Send via email/Slack
    # send_notification(report)
```

Run daily:
```bash
# crontab -e
0 8 * * * cd /opt/content-insights && python scripts/monitoring_report.py
```

---

## 🔍 Incident Response

### When Conformal Coverage < 85%

1. **Immediate**: Page on-call engineer
2. **Investigation**:
   - Check data drift metrics
   - Review recent prediction errors
   - Inspect input feature distributions
3. **Resolution**:
   - If data drift: Retrain model
   - If outliers: Add preprocessing step
   - If feature change: Update feature engineering
4. **Prevention**: Add weekly drift checks

### When Response Time > 1s

1. **Check**: Prometheus metrics for bottleneck
   - Model inference time?
   - Database query slow?
   - Network latency?
2. **Scale**: Increase replicas if CPU-bound
3. **Optimize**: Profile and optimize slow code path

### When Error Rate > 5%

1. **Logs**: Check application logs for errors
2. **Rollback**: If recent deployment, rollback
3. **Debug**: Check health endpoint for details
4. **Scale**: Increase resources if capacity issue

---

## 📈 SLO & SLI Definitions

### Service Level Objectives (SLOs)

| SLO | Target | Tool |
|-----|--------|------|
| API Availability | 99.9% | Uptime Robot |
| P95 Response Time | < 500ms | Prometheus |
| Error Rate | < 1% | Prometheus |
| Conformal Coverage | 90% ± 5% | Custom |

### Service Level Indicators (SLIs)

```yaml
SLIs:
  availability:
    metric: (successful_requests) / (total_requests)
    target: > 0.999
    window: 30 days

  latency:
    metric: P95(request_duration)
    target: < 0.5s
    window: 1 hour

  error_rate:
    metric: (error_requests) / (total_requests)
    target: < 0.01
    window: 1 hour

  model_coverage:
    metric: conformal_coverage
    target: 0.85 < value < 0.98
    window: 24 hours
```

---

## 🐛 Debugging Production Issues

### Enable verbose logging
```python
# Set log level
logging.getLogger("app").setLevel(logging.DEBUG)
```

### Access logs
```bash
# Docker
docker-compose -f docker-compose.prod.yml logs backend -f --tail=100

# Kubernetes
kubectl logs -n content-insights deployment/backend -f
```

### Database queries
```sql
-- PostgreSQL (MLflow backend)
SELECT experiment_name, run_id, param_key, param_value
FROM experiment_runs
ORDER BY start_time DESC
LIMIT 10;
```

---

## 📚 References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Alertmanager Setup](https://prometheus.io/docs/alerting/latest/overview/)
- [SLO Engineering](https://slo.dev/)
- [ML Monitoring Best Practices](https://blog.evidentlyai.com/)
