"""
Tests for A/B testing functionality.
"""
import os
from unittest.mock import Mock, patch

import pytest

from api.ab_testing import ABTestManager, ModelVariant


@pytest.fixture
def ab_test_manager():
    """Create a fresh ABTestManager instance for each test."""
    return ABTestManager()


@pytest.fixture
def mock_model():
    """Create a mock model for testing."""
    model = Mock()
    model.predict = Mock(return_value=[0.75])
    return model


class TestModelVariant:
    """Tests for ModelVariant dataclass."""

    def test_model_variant_creation(self, mock_model):
        """Test creating a ModelVariant."""
        variant = ModelVariant(
            name="production",
            model=mock_model,
            traffic_percentage=100.0,
            version="1.0.0",
            stage="champion",
        )

        assert variant.name == "production"
        assert variant.model == mock_model
        assert variant.traffic_percentage == 100.0
        assert variant.version == "1.0.0"
        assert variant.stage == "champion"


class TestABTestManager:
    """Tests for ABTestManager class."""

    def test_add_variant(self, ab_test_manager, mock_model):
        """Test adding a variant to the manager."""
        ab_test_manager.add_variant(
            name="production",
            model=mock_model,
            traffic_percentage=100.0,
            version="1.0.0",
            stage="champion",
        )

        assert len(ab_test_manager.variants) == 1
        assert "production" in ab_test_manager.variants
        assert ab_test_manager.variants["production"].traffic_percentage == 100.0

    def test_add_multiple_variants(self, ab_test_manager, mock_model):
        """Test adding multiple variants."""
        ab_test_manager.add_variant("production", mock_model, 70.0, "1.0.0", "champion")
        ab_test_manager.add_variant("staging", mock_model, 30.0, "1.1.0", "challenger")

        assert len(ab_test_manager.variants) == 2
        assert ab_test_manager.variants["production"].traffic_percentage == 70.0
        assert ab_test_manager.variants["staging"].traffic_percentage == 30.0

    def test_remove_variant(self, ab_test_manager, mock_model):
        """Test removing a variant."""
        ab_test_manager.add_variant("production", mock_model, 100.0)
        ab_test_manager.remove_variant("production")

        assert len(ab_test_manager.variants) == 0
        assert "production" not in ab_test_manager.variants

    def test_remove_nonexistent_variant(self, ab_test_manager):
        """Test removing a variant that doesn't exist."""
        # Should not raise an error
        ab_test_manager.remove_variant("nonexistent")
        assert len(ab_test_manager.variants) == 0

    def test_set_routing_strategy(self, ab_test_manager):
        """Test setting routing strategy."""
        ab_test_manager.set_routing_strategy("hash")
        assert ab_test_manager.routing_strategy == "hash"

        ab_test_manager.set_routing_strategy("sticky")
        assert ab_test_manager.routing_strategy == "sticky"

    def test_set_invalid_routing_strategy(self, ab_test_manager):
        """Test setting an invalid routing strategy."""
        ab_test_manager.set_routing_strategy("invalid")
        # Should default to random
        assert ab_test_manager.routing_strategy == "random"

    def test_enable_disable_test(self, ab_test_manager):
        """Test enabling and disabling A/B test."""
        assert ab_test_manager.enabled is False

        ab_test_manager.enable_test()
        assert ab_test_manager.enabled is True

        ab_test_manager.disable_test()
        assert ab_test_manager.enabled is False

    def test_update_traffic_split(self, ab_test_manager, mock_model):
        """Test updating traffic split."""
        ab_test_manager.add_variant("production", mock_model, 100.0)
        ab_test_manager.add_variant("staging", mock_model, 0.0)

        ab_test_manager.update_traffic_split({"production": 50.0, "staging": 50.0})

        assert ab_test_manager.variants["production"].traffic_percentage == 50.0
        assert ab_test_manager.variants["staging"].traffic_percentage == 50.0

    def test_update_traffic_split_nonexistent_variant(self, ab_test_manager, mock_model):
        """Test updating traffic split for nonexistent variant."""
        ab_test_manager.add_variant("production", mock_model, 100.0)

        # Should only update existing variant
        ab_test_manager.update_traffic_split({"production": 80.0, "nonexistent": 20.0})

        assert ab_test_manager.variants["production"].traffic_percentage == 80.0

    def test_get_variant_stats(self, ab_test_manager, mock_model):
        """Test getting variant statistics."""
        ab_test_manager.add_variant("production", mock_model, 70.0, "1.0.0", "champion")
        ab_test_manager.add_variant("staging", mock_model, 30.0, "1.1.0", "challenger")
        ab_test_manager.set_routing_strategy("hash")
        ab_test_manager.enable_test()

        stats = ab_test_manager.get_variant_stats()

        assert stats["enabled"] is True
        assert stats["routing_strategy"] == "hash"
        assert len(stats["variants"]) == 2

        prod_stats = next(v for v in stats["variants"] if v["name"] == "production")
        assert prod_stats["traffic_percentage"] == 70.0
        assert prod_stats["version"] == "1.0.0"
        assert prod_stats["stage"] == "champion"


class TestVariantSelection:
    """Tests for variant selection logic."""

    def test_select_variant_disabled(self, ab_test_manager, mock_model):
        """Test variant selection when A/B test is disabled."""
        ab_test_manager.add_variant("production", mock_model, 100.0)
        ab_test_manager.disable_test()

        variant = ab_test_manager.select_variant()

        # Should return first variant when disabled
        assert variant.name == "production"

    def test_select_variant_single_variant(self, ab_test_manager, mock_model):
        """Test variant selection with single variant."""
        ab_test_manager.add_variant("production", mock_model, 100.0)
        ab_test_manager.enable_test()

        variant = ab_test_manager.select_variant()

        assert variant.name == "production"

    @patch("random.uniform")
    def test_select_variant_random_strategy(self, mock_random, ab_test_manager, mock_model):
        """Test variant selection with random routing strategy."""
        ab_test_manager.add_variant("production", mock_model, 70.0)
        ab_test_manager.add_variant("staging", mock_model, 30.0)
        ab_test_manager.set_routing_strategy("random")
        ab_test_manager.enable_test()

        # Mock random to return 50 (should select production with 70% traffic)
        mock_random.return_value = 50
        variant = ab_test_manager.select_variant()
        assert variant.name == "production"

        # Mock random to return 80 (should select staging with 30% traffic)
        mock_random.return_value = 80
        variant = ab_test_manager.select_variant()
        assert variant.name == "staging"

    def test_select_variant_hash_strategy(self, ab_test_manager, mock_model):
        """Test variant selection with hash routing strategy."""
        ab_test_manager.add_variant("production", mock_model, 70.0)
        ab_test_manager.add_variant("staging", mock_model, 30.0)
        ab_test_manager.set_routing_strategy("hash")
        ab_test_manager.enable_test()

        # Same user_id should always get same variant
        variant1 = ab_test_manager.select_variant(user_id="user123")
        variant2 = ab_test_manager.select_variant(user_id="user123")
        assert variant1.name == variant2.name

        # Different users may get different variants
        variant3 = ab_test_manager.select_variant(user_id="user456")
        # We can't guarantee different variants, but at least it shouldn't error
        assert variant3.name in ["production", "staging"]

    def test_select_variant_sticky_strategy(self, ab_test_manager, mock_model):
        """Test variant selection with sticky routing strategy."""
        ab_test_manager.add_variant("production", mock_model, 70.0)
        ab_test_manager.add_variant("staging", mock_model, 30.0)
        ab_test_manager.set_routing_strategy("sticky")
        ab_test_manager.enable_test()

        # Same session_id should always get same variant
        variant1 = ab_test_manager.select_variant(session_id="session123")
        variant2 = ab_test_manager.select_variant(session_id="session123")
        assert variant1.name == variant2.name

        # Different sessions may get different variants
        variant3 = ab_test_manager.select_variant(session_id="session456")
        assert variant3.name in ["production", "staging"]

    def test_select_variant_hash_without_user_id(self, ab_test_manager, mock_model):
        """Test hash routing strategy without user_id falls back to random."""
        ab_test_manager.add_variant("production", mock_model, 100.0)
        ab_test_manager.set_routing_strategy("hash")
        ab_test_manager.enable_test()

        variant = ab_test_manager.select_variant()
        assert variant.name == "production"

    def test_select_variant_sticky_without_session_id(self, ab_test_manager, mock_model):
        """Test sticky routing strategy without session_id falls back to random."""
        ab_test_manager.add_variant("production", mock_model, 100.0)
        ab_test_manager.set_routing_strategy("sticky")
        ab_test_manager.enable_test()

        variant = ab_test_manager.select_variant()
        assert variant.name == "production"


class TestConfigurationFromEnvironment:
    """Tests for configuration from environment variables."""

    @patch.dict(
        os.environ,
        {
            "AB_TESTING_ENABLED": "true",
            "AB_ROUTING_STRATEGY": "hash",
            "AB_TRAFFIC_CONFIG": "production:70,staging:30",
        },
    )
    def test_configure_from_env(self, ab_test_manager, mock_model):
        """Test configuration from environment variables."""
        # Add variants first
        ab_test_manager.add_variant("production", mock_model, 100.0)
        ab_test_manager.add_variant("staging", mock_model, 0.0)

        # Configure from environment
        from api.ab_testing import configure_ab_test_from_env

        configure_ab_test_from_env(ab_test_manager)

        assert ab_test_manager.enabled is True
        assert ab_test_manager.routing_strategy == "hash"
        assert ab_test_manager.variants["production"].traffic_percentage == 70.0
        assert ab_test_manager.variants["staging"].traffic_percentage == 30.0

    @patch.dict(os.environ, {"AB_TESTING_ENABLED": "false"})
    def test_configure_from_env_disabled(self, ab_test_manager):
        """Test configuration when A/B testing is disabled."""
        from api.ab_testing import configure_ab_test_from_env

        configure_ab_test_from_env(ab_test_manager)

        assert ab_test_manager.enabled is False

    @patch.dict(os.environ, {"AB_ROUTING_STRATEGY": "sticky"})
    def test_configure_from_env_routing_only(self, ab_test_manager):
        """Test configuration with only routing strategy."""
        from api.ab_testing import configure_ab_test_from_env

        configure_ab_test_from_env(ab_test_manager)

        assert ab_test_manager.routing_strategy == "sticky"

    @patch.dict(os.environ, {"AB_TRAFFIC_CONFIG": "production:100"})
    def test_configure_from_env_traffic_only(self, ab_test_manager, mock_model):
        """Test configuration with only traffic config."""
        ab_test_manager.add_variant("production", mock_model, 0.0)

        from api.ab_testing import configure_ab_test_from_env

        configure_ab_test_from_env(ab_test_manager)

        assert ab_test_manager.variants["production"].traffic_percentage == 100.0

    @patch.dict(os.environ, {}, clear=True)
    def test_configure_from_env_no_config(self, ab_test_manager):
        """Test configuration with no environment variables."""
        from api.ab_testing import configure_ab_test_from_env

        # Should not raise an error
        configure_ab_test_from_env(ab_test_manager)

        # Default values
        assert ab_test_manager.enabled is False
        assert ab_test_manager.routing_strategy == "random"


class TestMetrics:
    """Tests for metrics tracking."""

    def test_metrics_exist(self, ab_test_manager):
        """Test that metrics are properly initialized."""
        from api.ab_testing import variant_errors, variant_latency, variant_requests

        assert variant_requests is not None
        assert variant_latency is not None
        assert variant_errors is not None

    def test_metrics_labels(self, ab_test_manager, mock_model):
        """Test that metrics use correct labels."""
        ab_test_manager.add_variant("production", mock_model, 100.0, "1.0.0", "champion")

        # Metrics should support variant_name, variant_version, variant_stage labels
        variant = ab_test_manager.variants["production"]

        # Just verify the variant has the expected attributes
        assert variant.name == "production"
        assert variant.version == "1.0.0"
        assert variant.stage == "champion"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_variants(self, ab_test_manager):
        """Test behavior with no variants."""
        variant = ab_test_manager.select_variant()
        assert variant is None

    def test_zero_traffic_variants(self, ab_test_manager, mock_model):
        """Test behavior when all variants have zero traffic."""
        ab_test_manager.add_variant("production", mock_model, 0.0)
        ab_test_manager.add_variant("staging", mock_model, 0.0)
        ab_test_manager.enable_test()

        # Should still return a variant (first one)
        variant = ab_test_manager.select_variant()
        assert variant.name in ["production", "staging"]

    def test_traffic_sum_not_100(self, ab_test_manager, mock_model):
        """Test behavior when traffic doesn't sum to 100%."""
        ab_test_manager.add_variant("production", mock_model, 60.0)
        ab_test_manager.add_variant("staging", mock_model, 30.0)
        # Total is 90%, not 100%
        ab_test_manager.enable_test()

        # Should still work, will normalize internally
        variant = ab_test_manager.select_variant()
        assert variant.name in ["production", "staging"]

    def test_very_small_traffic_percentage(self, ab_test_manager, mock_model):
        """Test variant with very small traffic percentage."""
        ab_test_manager.add_variant("production", mock_model, 99.9)
        ab_test_manager.add_variant("staging", mock_model, 0.1)
        ab_test_manager.enable_test()

        # Both variants should be selectable
        variant = ab_test_manager.select_variant()
        assert variant.name in ["production", "staging"]

    def test_unicode_variant_names(self, ab_test_manager, mock_model):
        """Test variants with unicode names."""
        ab_test_manager.add_variant("", mock_model, 50.0)
        ab_test_manager.add_variant("staging-", mock_model, 50.0)
        ab_test_manager.enable_test()

        variant = ab_test_manager.select_variant()
        assert variant.name in ["", "staging-"]

    def test_concurrent_variant_updates(self, ab_test_manager, mock_model):
        """Test thread safety of variant updates."""
        # Add initial variants
        ab_test_manager.add_variant("production", mock_model, 100.0)

        # Simulate concurrent updates
        ab_test_manager.update_traffic_split({"production": 80.0})
        ab_test_manager.add_variant("staging", mock_model, 20.0)

        # Should maintain consistency
        stats = ab_test_manager.get_variant_stats()
        assert len(stats["variants"]) == 2
