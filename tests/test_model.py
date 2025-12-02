"""Tests for the churn prediction model."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.data import generate_churn_data
from src.model import ChurnModel


class TestDataGeneration:
    """Test data generation functionality."""

    def test_generate_churn_data_shape(self):
        """Test that generated data has correct shape."""
        df = generate_churn_data(n_samples=100)
        assert df.shape[0] == 100
        assert df.shape[1] == 6  # 6 features including churn

    def test_generate_churn_data_columns(self):
        """Test that generated data has correct columns."""
        df = generate_churn_data(n_samples=50)
        expected_columns = [
            "tenure_months",
            "monthly_charges",
            "total_charges",
            "contract_type",
            "num_support_tickets",
            "churn",
        ]
        assert list(df.columns) == expected_columns

    def test_generate_churn_data_types(self):
        """Test that generated data has correct types."""
        df = generate_churn_data(n_samples=50)
        assert df["tenure_months"].dtype in ["int64", "int32"]
        assert df["monthly_charges"].dtype == "float64"
        assert df["total_charges"].dtype == "float64"
        assert df["contract_type"].dtype == "object"
        assert df["num_support_tickets"].dtype in ["int64", "int32"]
        assert df["churn"].dtype in ["int64", "int32"]

    def test_generate_churn_data_reproducible(self):
        """Test that data generation is reproducible with same random_state."""
        df1 = generate_churn_data(n_samples=100, random_state=42)
        df2 = generate_churn_data(n_samples=100, random_state=42)
        pd.testing.assert_frame_equal(df1, df2)


class TestChurnModel:
    """Test ChurnModel class."""

    @pytest.fixture
    def sample_data(self):
        """Generate sample data for testing."""
        df = generate_churn_data(n_samples=200, random_state=42)
        # Encode categorical features
        df_encoded = pd.get_dummies(df, columns=["contract_type"], drop_first=True)
        X = df_encoded.drop("churn", axis=1)
        y = df_encoded["churn"]
        return X, y

    def test_model_initialization(self):
        """Test that model initializes correctly."""
        model = ChurnModel(n_estimators=50, random_state=42)
        assert model.model.n_estimators == 50
        assert model.model.random_state == 42
        assert model.metrics == {}

    def test_model_training(self, sample_data):
        """Test that model trains and returns metrics."""
        X, y = sample_data
        model = ChurnModel(n_estimators=50, random_state=42)
        metrics = model.train(X, y)

        # Check that metrics are returned
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics

        # Check that metrics are reasonable (between 0 and 1)
        assert 0 <= metrics["accuracy"] <= 1
        assert 0 <= metrics["precision"] <= 1
        assert 0 <= metrics["recall"] <= 1

        # Check that metrics are stored
        assert model.metrics == metrics

    def test_model_prediction(self, sample_data):
        """Test that model can make predictions."""
        X, y = sample_data
        model = ChurnModel(n_estimators=50, random_state=42)
        model.train(X, y)

        # Make predictions
        predictions = model.predict(X[:10])

        # Check predictions shape and values
        assert len(predictions) == 10
        assert all(pred in [0, 1] for pred in predictions)

    def test_model_save_load(self, sample_data):
        """Test that model can be saved and loaded."""
        X, y = sample_data

        # Train original model
        original_model = ChurnModel(n_estimators=50, random_state=42)
        original_model.train(X, y)
        original_predictions = original_model.predict(X[:10])

        # Save model to temporary file
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "test_model.pkl"
            original_model.save(model_path)

            # Load model
            loaded_model = ChurnModel.load(model_path)
            loaded_predictions = loaded_model.predict(X[:10])

            # Check that predictions match
            assert all(original_predictions == loaded_predictions)

    def test_model_consistency(self, sample_data):
        """Test that model produces consistent results with same random_state."""
        X, y = sample_data

        # Train two models with same parameters
        model1 = ChurnModel(n_estimators=50, random_state=42)
        model2 = ChurnModel(n_estimators=50, random_state=42)

        metrics1 = model1.train(X, y)
        metrics2 = model2.train(X, y)

        # Metrics should be identical
        assert metrics1["accuracy"] == metrics2["accuracy"]
        assert metrics1["precision"] == metrics2["precision"]
        assert metrics1["recall"] == metrics2["recall"]
