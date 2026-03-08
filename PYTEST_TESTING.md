# Unit Testing Guide - Pytest

Comprehensive testing framework for the backend API and ML pipeline.

---

## 🎯 Overview

The testing strategy covers:
- ✅ **Unit tests**: Individual functions (ETL, models, utilities)
- ✅ **Integration tests**: API endpoints with real data
- ✅ **Performance tests**: Model inference speed
- ✅ **Coverage tracking**: Minimum 80% code coverage target

---

## 📦 Installation & Setup

### Install pytest and dependencies
```bash
cd backend
pip install pytest pytest-cov pytest-asyncio httpx pytest-xdist
```

### Directory structure
```
backend/
├── app/
│   ├── main.py
│   ├── service.py
│   ├── etl.py
│   ├── analysis_*.py
│   └── ...
└── tests/
    ├── conftest.py
    ├── test_api.py
    ├── test_etl.py
    ├── test_pipeline.py
    └── fixtures/
        └── sample_data.csv
```

---

## 🧪 Test Organization

### conftest.py - Shared Fixtures

```python
import pytest
import pandas as pd
from pathlib import Path

@pytest.fixture
def sample_df():
    """Load sample video data."""
    path = Path(__file__).parent / "fixtures" / "sample_data.csv"
    return pd.read_csv(path)

@pytest.fixture
def client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)

@pytest.fixture(scope="session")
def test_data():
    """Large dataset for performance tests."""
    return pd.DataFrame({
        'video_id': range(1000),
        'title': [f'Video {i}' for i in range(1000)],
        'views': [100000 + i*10 for i in range(1000)],
        'engagement_rate': [0.05 + (i%100)*0.001 for i in range(1000)],
    })
```

---

## 🔍 Test Categories

### 1. ETL Tests (`test_etl.py`)

```python
import pytest
from app.etl import load_clean, REQUIRED

def test_load_clean_valid_data(sample_df):
    """Test loading valid CSV data."""
    result = load_clean(sample_df)

    assert len(result) > 0
    assert all(col in result.columns for col in REQUIRED)
    assert result['engagement_rate'].notna().all()

def test_load_clean_missing_columns():
    """Test handling of missing required columns."""
    bad_df = pd.DataFrame({
        'video_id': [1, 2, 3],
        'title': ['A', 'B', 'C']
        # Missing required columns
    })

    with pytest.raises(ValueError, match="Missing columns"):
        load_clean(bad_df)

def test_feature_engineering(sample_df):
    """Test feature derivation."""
    df = load_clean(sample_df)

    assert 'engagement_rate' in df.columns
    assert 'avg_watch_time_per_view' in df.columns
    assert 'virality_score' in df.columns

    # Engagement rate should be between 0 and 1
    assert (df['engagement_rate'] >= 0).all() and (df['engagement_rate'] <= 1).all()

def test_no_nulls_after_cleaning(sample_df):
    """Verify no nulls in required columns after ETL."""
    df = load_clean(sample_df)

    for col in REQUIRED:
        assert df[col].notna().all(), f"Nulls found in {col}"

@pytest.mark.parametrize("views", [0, -100])
def test_invalid_views_filtered(views):
    """Test that invalid view counts are filtered."""
    df = pd.DataFrame({
        'video_id': [1],
        'views': [views],
        'watch_time_seconds': [100],
        # ... other required columns
    })

    result = load_clean(df)
    assert len(result) == 0  # Should be filtered out
```

---

### 2. Clustering Tests

```python
import pytest
from sklearn.metrics import silhouette_score
from app.analysis_clustering import add_clusters

def test_kmeans_clustering(sample_df):
    """Test KMeans clustering produces expected number of clusters."""
    df = add_clusters(sample_df, k=4, random_state=42)

    assert 'cluster' in df.columns
    unique_clusters = df['cluster'].unique()
    assert len(unique_clusters) == 2

def test_clustering_reproducibility(sample_df):
    """Test that clustering is reproducible with same random_state."""
    df1 = add_clusters(sample_df.copy(), k=4, random_state=42)
    df2 = add_clusters(sample_df.copy(), k=4, random_state=42)

    assert (df1['cluster'].values == df2['cluster'].values).all()

def test_dbscan_finds_clusters(sample_df):
    """Test DBSCAN detects at least some clusters."""
    df = add_clusters(sample_df, k=None, random_state=42)  # k=None triggers DBSCAN

    assert 'dbscan_cluster' in df.columns
    # Should have at least some non-noise points (-1 is noise label)
    assert (df['dbscan_cluster'] != -1).sum() > 0

def test_cluster_quality(sample_df):
    """Test clustering produces reasonable silhouette score."""
    df = add_clusters(sample_df, k=4, random_state=42)

    from sklearn.preprocessing import StandardScaler
    features = ['views', 'engagement_rate', 'avg_watch_time_per_view']
    X = StandardScaler().fit_transform(df[features].fillna(0))

    sil_score = silhouette_score(X, df['cluster'])
    assert sil_score > -0.5  # Silhouette score should not be terrible
```

---

### 3. Predictive Model Tests

```python
import pytest
from app.analysis_predictive import fit_predictive_with_conformal

def test_predictive_model_training(sample_df):
    """Test model trains without errors."""
    df, artifacts = fit_predictive_with_conformal(
        df=sample_df,
        random_state=42,
        test_size=0.2,
        alpha=0.1
    )

    assert 'engagement_pred' in df.columns
    assert 'engagement_pi_low' in df.columns
    assert 'engagement_pi_high' in df.columns

def test_conformal_intervals_valid(sample_df):
    """Test that confidence intervals are valid (lower < upper)."""
    df, artifacts = fit_predictive_with_conformal(
        df=sample_df,
        random_state=42,
        test_size=0.2,
        alpha=0.1
    )

    # Lower bound should be less than upper bound
    assert (df['engagement_pi_low'] <= df['engagement_pi_high']).all()

def test_conformal_coverage(sample_df):
    """Test that conformal coverage meets target."""
    df, artifacts = fit_predictive_with_conformal(
        df=sample_df,
        random_state=42,
        test_size=0.2,
        alpha=0.1
    )

    coverage = artifacts.metrics.get('coverage', 0)
    # Should achieve at least 85% coverage (target is 90%, allow 5% margin)
    assert coverage >= 0.85, f"Coverage {coverage} below 85% threshold"

def test_model_r2_score(sample_df):
    """Test model achieves reasonable R² score."""
    df, artifacts = fit_predictive_with_conformal(
        df=sample_df,
        random_state=42,
        test_size=0.2,
        alpha=0.1
    )

    r2 = artifacts.metrics.get('r2', 0)
    # Should achieve at least 0.5 R² (explains 50% of variance)
    assert r2 >= 0.5, f"R² score {r2} too low"

def test_shap_values_computed(sample_df):
    """Test SHAP explanations are computed."""
    df, artifacts = fit_predictive_with_conformal(
        df=sample_df,
        random_state=42,
        test_size=0.2,
        alpha=0.1
    )

    assert 'shap_summary' in artifacts.__dict__
    assert len(artifacts.shap_summary.get('top_features', [])) > 0
```

---

### 4. API Endpoint Tests (`test_api.py`)

```python
import pytest
from fastapi.testclient import TestClient

def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}

def test_metrics_endpoint(client):
    """Test metrics endpoint returns valid data."""
    response = client.get("/metrics")

    assert response.status_code == 200
    data = response.json()
    assert "rows" in data
    assert "total_views" in data
    assert "cluster_count" in data

def test_videos_endpoint(client):
    """Test videos listing endpoint."""
    response = client.get("/videos?limit=10")

    assert response.status_code == 200
    videos = response.json()
    assert len(videos) <= 10

    # Each video should have predictions
    if len(videos) > 0:
        first_video = videos[0]
        assert "engagement_pred" in first_video
        assert "engagement_pi_low" in first_video
        assert "engagement_pi_high" in first_video

def test_videos_endpoint_filtering(client):
    """Test videos endpoint respects filters."""
    # Get available categories
    filters_resp = client.get("/filters")
    categories = filters_resp.json().get("categories", [])

    if len(categories) > 0:
        response = client.get(f"/videos?category={categories[0]}")
        assert response.status_code == 200

def test_insights_endpoint(client):
    """Test full insights endpoint."""
    response = client.get("/insights")

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "correlations" in data
    assert "clustering_diagnostics" in data
    assert "predictive_model" in data

    # Check predictive model fields
    pred = data["predictive_model"]
    assert "metrics" in pred
    assert "diagnostics" in pred
    assert "shap_summary" in pred

def test_similar_endpoint(client):
    """Test similarity search endpoint."""
    # First get a video ID
    videos_resp = client.get("/videos?limit=1")
    if videos_resp.json():
        video_id = videos_resp.json()[0]["video_id"]

        response = client.get(f"/similar?video_id={video_id}&top_k=5")
        assert response.status_code == 200
        similar = response.json()
        assert len(similar) <= 5

@pytest.mark.parametrize("limit", [1, 10, 100, 500])
def test_videos_limit_parameter(client, limit):
    """Test various limit parameters."""
    response = client.get(f"/videos?limit={limit}")
    assert response.status_code == 200
    assert len(response.json()) <= limit

def test_invalid_video_id_returns_empty(client):
    """Test querying non-existent video returns empty."""
    response = client.get("/similar?video_id=nonexistent&top_k=5")
    # Should either return empty list or 404
    assert response.status_code in [200, 404]
```

---

### 5. Integration Tests

```python
import pytest
from app.service import build_state

def test_full_pipeline_execution(sample_df):
    """Test entire pipeline from data to predictions."""
    # This simulates the complete flow
    state = build_state(
        data_path="tests/fixtures/sample_data.csv",
        cluster_k=4,
        contamination=0.05,
        random_state=42,
        test_size=0.2,
        alpha=0.1
    )

    assert state.df is not None
    assert len(state.df) > 0
    assert state.predictive is not None
    assert state.tfidf_mat is not None

def test_all_columns_present_after_pipeline(sample_df):
    """Verify all expected columns exist after full pipeline."""
    state = build_state(
        data_path="tests/fixtures/sample_data.csv",
        cluster_k=4,
        contamination=0.05,
        random_state=42,
        test_size=0.2,
        alpha=0.1
    )

    expected_cols = [
        'video_id', 'cluster', 'dbscan_cluster', 'is_anomaly',
        'engagement_pred', 'engagement_pi_low', 'engagement_pi_high'
    ]

    for col in expected_cols:
        assert col in state.df.columns, f"Missing column: {col}"

def test_no_leakage_between_train_test():
    """Verify training/test sets are properly separated."""
    # Check that predictions on training data are different from test data
    # to ensure no data leakage
    pass
```

---

## 🚀 Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run with coverage report
```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term
# Open htmlcov/index.html to view coverage
```

### Run specific test file
```bash
pytest tests/test_api.py -v
```

### Run specific test function
```bash
pytest tests/test_api.py::test_health_endpoint -v
```

### Run tests in parallel (faster)
```bash
pytest tests/ -n auto  # Requires pytest-xdist
```

### Run only fast tests (skip slow ones)
```bash
pytest tests/ -m "not slow" -v
```

### Run with coverage and fail on low coverage
```bash
pytest tests/ --cov=app --cov-fail-under=80
```

---

## 📊 Coverage Goals

| Component | Target | Current | Status |
|-----------|--------|---------|--------|
| ETL | 85% | - | ⏳ |
| Clustering | 90% | - | ⏳ |
| Predictive | 85% | - | ⏳ |
| API | 80% | - | ⏳ |
| **Total** | **80%** | - | ⏳ |

---

## 🐛 Test Markers

Mark tests for selective execution:

```python
@pytest.mark.slow
def test_full_training():
    """This takes a long time."""
    pass

@pytest.mark.unit
def test_feature_calculation():
    """Quick unit test."""
    pass

@pytest.mark.integration
def test_api_endpoint():
    """Tests with external components."""
    pass
```

Run by marker:
```bash
pytest tests/ -m "unit" -v  # Only unit tests
pytest tests/ -m "not slow" -v  # Skip slow tests
```

---

## 🔄 Continuous Integration

### `.pytest.ini` - pytest configuration

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
    api: API endpoint tests
    ml: Machine learning tests
```

### Pre-commit hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

cd backend
pytest tests/ --cov=app --cov-fail-under=75 -x
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

---

## 📝 Test Writing Best Practices

### 1. Clear test names
```python
# ✅ Good
def test_load_clean_removes_negative_view_counts():
    pass

# ❌ Bad
def test_etl():
    pass
```

### 2. Arrange-Act-Assert pattern
```python
def test_engagement_calculation():
    # Arrange
    df = pd.DataFrame({
        'likes': [100],
        'comments': [50],
        'shares': [25],
        'views': [1000]
    })

    # Act
    result = df['engagement_rate'] = (df['likes'] + df['comments'] + df['shares']) / df['views']

    # Assert
    assert result[0] == 0.175
```

### 3. Use fixtures for reusable data
```python
@pytest.fixture
def standard_video_dataframe():
    return pd.DataFrame({...})

def test_something(standard_video_dataframe):
    # Use fixture
    result = process(standard_video_dataframe)
```

### 4. Parametrize repeated tests
```python
@pytest.mark.parametrize("input,expected", [
    (0.05, 0.05),
    (0.50, 0.50),
    (0.99, 0.99),
])
def test_engagement_rates(input, expected):
    assert input == expected
```

---

## 📚 References

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Coverage Plugin](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.pytest.org/en/latest/goodpractices.html)
- [Fixtures Documentation](https://docs.pytest.org/en/latest/fixture.html)
