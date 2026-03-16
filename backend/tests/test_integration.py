"""Integration test — validates full pipeline from ETL through /insights response shape."""

from pathlib import Path

import pytest

from app.etl import load_clean
from app.analysis_clustering import add_clusters
from app.analysis_anomaly import add_anomalies
from app.analysis_predictive import fit_predictive_with_conformal
from app.service import insights


DATA_PATH = Path(__file__).resolve().parents[3] / "sample_videos.csv"
RANDOM_STATE = 42


@pytest.fixture(scope="module")
def pipeline_result():
    """Run the full pipeline once for this test module."""
    df = load_clean(str(DATA_PATH))
    df = add_clusters(df, k=2, random_state=RANDOM_STATE)
    df = add_anomalies(df, contamination=0.05, random_state=RANDOM_STATE)
    df, pred = fit_predictive_with_conformal(
        df=df, random_state=RANDOM_STATE, test_size=0.2, alpha=0.1
    )
    return df, pred


class TestFullPipeline:
    """End-to-end validation that the pipeline produces correct output shapes."""

    def test_pipeline_adds_required_columns(self, pipeline_result):
        df, _ = pipeline_result
        required = [
            "cluster", "dbscan_cluster", "is_anomaly",
            "engagement_pred", "engagement_pi_low", "engagement_pi_high",
        ]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_predictive_metrics_has_acceptance_fields(self, pipeline_result):
        _, pred = pipeline_result
        m = pred.metrics
        required_keys = [
            "mae", "rmse", "r2", "coverage",
            "naive_mae", "naive_rmse", "naive_r2",
            "mae_uplift_vs_naive", "model_beats_naive", "scientific_acceptance",
            "target_coverage", "coverage_error_abs",
        ]
        for key in required_keys:
            assert key in m, f"Missing metric: {key}"

    def test_acceptance_is_boolean(self, pipeline_result):
        _, pred = pipeline_result
        assert isinstance(pred.metrics["scientific_acceptance"], bool)
        assert isinstance(pred.metrics["model_beats_naive"], bool)

    def test_metrics_values_are_finite(self, pipeline_result):
        _, pred = pipeline_result
        import math
        for key in ["mae", "rmse", "naive_mae", "naive_rmse", "coverage"]:
            assert math.isfinite(pred.metrics[key]), f"{key} is not finite"

    def test_insights_response_shape(self, pipeline_result):
        df, pred = pipeline_result
        result = insights(df, pred)
        assert "predictive_model" in result
        assert "metrics" in result["predictive_model"]
        assert "top_feature_importances" in result["predictive_model"]
        assert "clustering_diagnostics" in result
        assert "anomaly_examples" in result
        assert "forecastability" in result

    def test_forecastability_metrics_present(self, pipeline_result):
        df, pred = pipeline_result
        result = insights(df, pred)
        fc = result["forecastability"]
        expected_keys = [
            "spectral_entropy", "foreca_score",
            "permutation_entropy", "hurst_exponent", "variance_ratio",
        ]
        for key in expected_keys:
            assert key in fc, f"Missing forecastability metric: {key}"
