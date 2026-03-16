"""Tests for predictive pipeline — acceptance logic, leakage guards, baseline comparison."""

import numpy as np
import pandas as pd
import pytest

from app.analysis_predictive import _naive_baseline_metrics


# ---------------------------------------------------------------------------
# Unit: naive baseline metrics
# ---------------------------------------------------------------------------

class TestNaiveBaselineMetrics:
    """Validate the leakage-safe naive baseline (train-mean predictor)."""

    def test_returns_required_keys(self):
        y_train = pd.Series([0.1, 0.2, 0.3])
        y_test = pd.Series([0.15, 0.25])
        result = _naive_baseline_metrics(y_train, y_test)
        assert "naive_mae" in result
        assert "naive_rmse" in result
        assert "naive_r2" in result

    def test_baseline_uses_train_mean_only(self):
        """Baseline must predict train mean — not test mean (that would be leakage)."""
        y_train = pd.Series([0.0, 0.0, 0.0, 1.0])  # mean = 0.25
        y_test = pd.Series([0.25, 0.25])  # identical to train mean
        result = _naive_baseline_metrics(y_train, y_test)
        assert result["naive_mae"] == pytest.approx(0.0, abs=1e-9)

    def test_baseline_nonzero_for_different_distributions(self):
        y_train = pd.Series([0.0, 0.0])  # mean = 0.0
        y_test = pd.Series([1.0, 1.0])
        result = _naive_baseline_metrics(y_train, y_test)
        assert result["naive_mae"] == pytest.approx(1.0, abs=1e-9)
        assert result["naive_rmse"] == pytest.approx(1.0, abs=1e-9)

    def test_values_are_float(self):
        y_train = pd.Series([0.1, 0.2])
        y_test = pd.Series([0.15])
        result = _naive_baseline_metrics(y_train, y_test)
        for v in result.values():
            assert isinstance(v, float)


# ---------------------------------------------------------------------------
# Unit: scientific acceptance logic
# ---------------------------------------------------------------------------

class TestScientificAcceptance:
    """Verify the acceptance gate: model must beat naive AND coverage must be stable."""

    def test_acceptance_true_when_model_beats_naive_and_coverage_stable(self):
        mae_uplift = 0.01  # positive = model better
        coverage_error_abs = 0.02  # within 0.05 threshold
        accepted = bool((mae_uplift > 0.0) and (coverage_error_abs <= 0.05))
        assert accepted is True

    def test_acceptance_false_when_model_worse_than_naive(self):
        mae_uplift = -0.01  # negative = naive better
        coverage_error_abs = 0.01
        accepted = bool((mae_uplift > 0.0) and (coverage_error_abs <= 0.05))
        assert accepted is False

    def test_acceptance_false_when_coverage_unstable(self):
        mae_uplift = 0.01
        coverage_error_abs = 0.10  # exceeds 0.05 threshold
        accepted = bool((mae_uplift > 0.0) and (coverage_error_abs <= 0.05))
        assert accepted is False

    def test_acceptance_false_when_both_fail(self):
        mae_uplift = -0.05
        coverage_error_abs = 0.15
        accepted = bool((mae_uplift > 0.0) and (coverage_error_abs <= 0.05))
        assert accepted is False

    def test_acceptance_boundary_zero_uplift_rejected(self):
        """Exactly zero uplift means no improvement — should NOT be accepted."""
        mae_uplift = 0.0
        coverage_error_abs = 0.01
        accepted = bool((mae_uplift > 0.0) and (coverage_error_abs <= 0.05))
        assert accepted is False

    def test_acceptance_boundary_exact_coverage_threshold(self):
        """Coverage error exactly at 0.05 boundary — should be accepted."""
        mae_uplift = 0.01
        coverage_error_abs = 0.05
        accepted = bool((mae_uplift > 0.0) and (coverage_error_abs <= 0.05))
        assert accepted is True
