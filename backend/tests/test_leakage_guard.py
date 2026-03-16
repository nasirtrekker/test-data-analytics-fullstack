"""Leakage regression guard — ensures no post-publication features sneak into the model.

This test should FAIL if someone accidentally adds engagement-derived columns
(views, likes, comments, shares, watch_time, engagement_rate, etc.) as model inputs.
"""

from app.feature_utils import SAFE_NUMERIC_FEATURES, SAFE_CATEGORICAL_FEATURES, TEXT_FEATURE

# Columns that must NEVER appear as model features (post-publication engagement)
FORBIDDEN_FEATURES = {
    "views", "likes", "comments", "shares",
    "watch_time_seconds", "engagement_rate",
    "avg_watch_time_per_view", "like_rate", "comment_rate", "share_rate",
    "virality_score", "total_interactions",
}


class TestLeakageGuard:
    """Prevent re-introduction of target-derived features into the predictive model."""

    def test_no_forbidden_features_in_safe_numeric(self):
        overlap = set(SAFE_NUMERIC_FEATURES) & FORBIDDEN_FEATURES
        assert overlap == set(), f"Leakage detected in SAFE_NUMERIC_FEATURES: {overlap}"

    def test_no_forbidden_features_in_safe_categorical(self):
        overlap = set(SAFE_CATEGORICAL_FEATURES) & FORBIDDEN_FEATURES
        assert overlap == set(), f"Leakage detected in SAFE_CATEGORICAL_FEATURES: {overlap}"

    def test_text_feature_is_not_engagement(self):
        assert TEXT_FEATURE not in FORBIDDEN_FEATURES

    def test_safe_features_are_pre_publication_only(self):
        """All safe numeric features should be derivable from title + publish_date."""
        allowed_prefixes = {
            "title_", "avg_word_", "publish_", "month_", "dow_",
        }
        for feat in SAFE_NUMERIC_FEATURES:
            assert any(feat.startswith(p) for p in allowed_prefixes), (
                f"Feature '{feat}' does not look like a pre-publication feature"
            )

    def test_feature_count_is_bounded(self):
        """Guard against feature set growing without review."""
        total = len(SAFE_NUMERIC_FEATURES) + len(SAFE_CATEGORICAL_FEATURES) + 1  # +1 for text
        assert total <= 15, (
            f"Feature count ({total}) exceeds expected bound. "
            "Review any new features for leakage before increasing."
        )
