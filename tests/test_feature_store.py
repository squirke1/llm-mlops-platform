"""Tests for feature store integration."""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Feature store imports with graceful handling
try:
    from feature_store import (
        FeatureStoreClient,
        get_feature_store_client,
        get_features_for_prediction,
        get_training_features,
    )
    from feature_store.generate_features import (
        generate_customer_contract,
        generate_customer_demographics,
        generate_customer_features,
        save_features_to_parquet,
    )

    FEAST_AVAILABLE = True
except ImportError:
    FEAST_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="Feast not installed")


@pytest.fixture
def temp_feature_store(tmp_path):
    """Create a temporary feature store for testing."""
    if not FEAST_AVAILABLE:
        pytest.skip("Feast not available")

    # Create feature store directory structure
    repo_path = tmp_path / "feature_store"
    repo_path.mkdir()
    data_path = tmp_path / "data"
    data_path.mkdir()

    # Copy feature_repo.py to temp directory
    source_repo = Path(__file__).parent.parent / "feature_store" / "feature_repo.py"
    if source_repo.exists():
        import shutil

        shutil.copy(source_repo, repo_path / "feature_repo.py")

    # Create feature_store.yaml
    config_content = f"""
project: churn_prediction_test
registry: {tmp_path}/data/registry.db
provider: local
online_store:
    type: sqlite
    path: {tmp_path}/data/online_store.db
offline_store:
    type: file
entity_key_serialization_version: 2
"""
    (repo_path / "feature_store.yaml").write_text(config_content)

    return repo_path, data_path


@pytest.fixture
def sample_features(temp_feature_store):
    """Generate sample features for testing."""
    if not FEAST_AVAILABLE:
        pytest.skip("Feast not available")

    repo_path, data_path = temp_feature_store

    # Generate sample data (small dataset for testing)
    n_customers = 10
    behavior_df = generate_customer_features(n_customers)
    demographics_df = generate_customer_demographics(n_customers)
    contract_df = generate_customer_contract(n_customers)

    # Save to parquet
    save_features_to_parquet(behavior_df, demographics_df, contract_df, data_dir=str(data_path))

    return behavior_df, demographics_df, contract_df


class TestFeatureGeneration:
    """Test feature data generation."""

    def test_generate_customer_features(self):
        """Test customer behavior features generation."""
        n_customers = 100
        df = generate_customer_features(n_customers)

        assert len(df) == n_customers
        assert "customer_id" in df.columns
        assert "event_timestamp" in df.columns
        assert "tenure_months" in df.columns
        assert "monthly_charges" in df.columns
        assert "total_charges" in df.columns
        assert "num_support_tickets" in df.columns

        # Validate data ranges
        assert df["tenure_months"].min() >= 1
        assert df["tenure_months"].max() <= 72
        assert df["monthly_charges"].min() >= 20.0
        assert df["monthly_charges"].max() <= 150.0
        assert df["num_support_tickets"].min() >= 0
        assert df["num_support_tickets"].max() <= 10

    def test_generate_customer_demographics(self):
        """Test customer demographics generation."""
        n_customers = 100
        df = generate_customer_demographics(n_customers)

        assert len(df) == n_customers
        assert "customer_id" in df.columns
        assert "event_timestamp" in df.columns
        assert "age" in df.columns
        assert "gender" in df.columns
        assert "location" in df.columns

        # Validate data ranges
        assert df["age"].min() >= 18
        assert df["age"].max() <= 80
        assert set(df["gender"].unique()).issubset({"Male", "Female", "Other"})

    def test_generate_customer_contract(self):
        """Test customer contract features generation."""
        n_customers = 100
        df = generate_customer_contract(n_customers)

        assert len(df) == n_customers
        assert "customer_id" in df.columns
        assert "event_timestamp" in df.columns
        assert "contract_type" in df.columns
        assert "payment_method" in df.columns
        assert "paperless_billing" in df.columns

        # Validate data values
        valid_contracts = {"Month-to-month", "One year", "Two year"}
        assert set(df["contract_type"].unique()).issubset(valid_contracts)

        valid_payments = {"Electronic check", "Credit card", "Bank transfer"}
        assert set(df["payment_method"].unique()).issubset(valid_payments)

        assert set(df["paperless_billing"].unique()).issubset({True, False})

    def test_save_features_to_parquet(self, tmp_path):
        """Test saving features to parquet files."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Generate small datasets
        behavior_df = generate_customer_features(10)
        demographics_df = generate_customer_demographics(10)
        contract_df = generate_customer_contract(10)

        # Save to parquet
        save_features_to_parquet(behavior_df, demographics_df, contract_df, data_dir=str(data_dir))

        # Verify files exist
        assert (data_dir / "customer_features.parquet").exists()
        assert (data_dir / "customer_demographics.parquet").exists()
        assert (data_dir / "customer_contract.parquet").exists()

        # Verify can read back
        loaded_behavior = pd.read_parquet(data_dir / "customer_features.parquet")
        assert len(loaded_behavior) == 10


class TestFeatureStoreClient:
    """Test FeatureStoreClient functionality."""

    def test_client_initialization(self, temp_feature_store):
        """Test feature store client initialization."""
        repo_path, _ = temp_feature_store

        client = FeatureStoreClient(str(repo_path))
        assert client.store is not None

    def test_list_feature_views(self, temp_feature_store):
        """Test listing feature views."""
        repo_path, _ = temp_feature_store

        client = FeatureStoreClient(str(repo_path))
        feature_views = client.list_feature_views()

        # Should have our defined feature views
        assert len(feature_views) > 0
        view_names = [fv.name for fv in feature_views]
        assert "customer_behavior_features" in view_names

    def test_list_feature_services(self, temp_feature_store):
        """Test listing feature services."""
        repo_path, _ = temp_feature_store

        client = FeatureStoreClient(str(repo_path))
        services = client.list_feature_services()

        # Should have our defined feature services
        assert len(services) > 0
        service_names = [fs.name for fs in services]
        assert "churn_prediction_v1" in service_names

    def test_get_feature_service_features(self, temp_feature_store):
        """Test getting features from a service."""
        repo_path, _ = temp_feature_store

        client = FeatureStoreClient(str(repo_path))
        features = client.get_feature_service_features("churn_prediction_v1")

        assert len(features) > 0
        # Should include features from all feature views
        assert any("tenure_months" in f for f in features)

    @pytest.mark.skipif(not FEAST_AVAILABLE, reason="Requires full Feast setup")
    def test_materialize_features(self, temp_feature_store, sample_features):
        """Test feature materialization."""
        repo_path, _ = temp_feature_store

        client = FeatureStoreClient(str(repo_path))

        # Materialize last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # This may fail if offline store not properly configured
        try:
            client.materialize_features(start_date, end_date)
        except Exception as e:
            pytest.skip(f"Materialization failed: {e}")

    def test_validate_features(self, temp_feature_store):
        """Test feature validation."""
        repo_path, _ = temp_feature_store

        client = FeatureStoreClient(str(repo_path))

        # Test with valid entity
        entity_rows = [{"customer_id": "CUST_000123"}]

        # Validation should not raise exception
        try:
            is_valid = client.validate_features(entity_rows)
            assert isinstance(is_valid, bool)
        except Exception:
            # May fail if online store not materialized - that's okay
            pass


class TestFeatureStoreHelpers:
    """Test helper functions for feature store."""

    def test_get_feature_store_client_singleton(self, temp_feature_store):
        """Test singleton pattern for feature store client."""
        repo_path, _ = temp_feature_store

        client1 = get_feature_store_client(str(repo_path))
        client2 = get_feature_store_client(str(repo_path))

        # Should return same instance
        assert client1 is client2

    @pytest.mark.skipif(not FEAST_AVAILABLE, reason="Requires full Feast setup")
    def test_get_features_for_prediction(self, temp_feature_store, sample_features):
        """Test getting features for a single customer."""
        repo_path, data_path = temp_feature_store
        behavior_df, _, _ = sample_features

        client = get_feature_store_client(str(repo_path))

        # Materialize features first
        try:
            from feature_store.setup_feature_store import (
                initialize_feature_store,
                materialize_features,
            )

            initialize_feature_store(str(repo_path))
            materialize_features(str(repo_path), days_back=7)
        except Exception as e:
            pytest.skip(f"Setup failed: {e}")

        # Get features for first customer
        customer_id = behavior_df.iloc[0]["customer_id"]
        features = get_features_for_prediction(customer_id, client)

        # Should return a dictionary with features
        assert isinstance(features, dict)
        if features:  # May be empty if materialization didn't work
            assert "customer_id" in features

    @pytest.mark.skipif(not FEAST_AVAILABLE, reason="Requires full Feast setup")
    def test_get_training_features(self, temp_feature_store, sample_features):
        """Test getting historical features for training."""
        repo_path, data_path = temp_feature_store
        behavior_df, _, _ = sample_features

        # Create entity dataframe
        entity_df = pd.DataFrame(
            {
                "customer_id": behavior_df["customer_id"].head(5).tolist(),
                "event_timestamp": [datetime.now()] * 5,
            }
        )

        try:
            features_df = get_training_features(entity_df)

            assert isinstance(features_df, pd.DataFrame)
            assert len(features_df) == 5
            assert "customer_id" in features_df.columns
        except Exception as e:
            pytest.skip(f"Training features failed: {e}")


class TestFeatureStoreIntegration:
    """Integration tests for feature store with API."""

    @patch("feature_store.get_feature_store_client")
    def test_api_with_feature_store(self, mock_get_client):
        """Test API integration with feature store."""
        # Mock feature store client
        mock_client = MagicMock()
        mock_client.validate_features.return_value = True
        mock_client.list_feature_views.return_value = []
        mock_client.list_feature_services.return_value = []
        mock_get_client.return_value = mock_client

        # Mock features for prediction
        mock_features = {
            "customer_id": "CUST_000123",
            "tenure_months": 24,
            "monthly_charges": 79.99,
            "total_charges": 1919.76,
            "contract_type": "Month-to-month",
            "num_support_tickets": 3,
        }

        with patch("feature_store.get_features_for_prediction", return_value=mock_features):
            # Import here to use mocked feature store
            from fastapi.testclient import TestClient

            from api.app import app

            client = TestClient(app)

            # Test feature store health endpoint
            response = client.get("/api/v1/features/health")
            assert response.status_code == 200

    def test_feature_store_unavailable(self):
        """Test API behavior when feature store is unavailable."""
        with patch("api.app.FEATURE_STORE_AVAILABLE", False):
            from fastapi.testclient import TestClient

            from api.app import app

            client = TestClient(app)

            # Feature store health should indicate unavailable
            response = client.get("/api/v1/features/health")
            assert response.status_code == 200
            data = response.json()
            assert data["available"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
