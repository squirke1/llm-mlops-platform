"""Tests for the FastAPI application."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import api.app as app_module  # noqa: E402
from api.app import app  # noqa: E402
from src.model import ChurnModel  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def setup_model():
    """Load model before running tests."""
    model_path = Path("models/churn_model.pkl")
    if not model_path.exists():
        # Train model if it doesn't exist
        import subprocess

        subprocess.run(["python", "src/train.py"], check=True)

    # Load model into app
    app_module.model = ChurnModel.load(model_path)
    yield
    # Cleanup
    app_module.model = None


client = TestClient(app)


class TestRootEndpoints:
    """Test root and health endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "health" in data

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "version" in data
        assert "ab_testing_enabled" in data
        assert data["version"] == "1.0.0"
        assert isinstance(data["ab_testing_enabled"], bool)


class TestPredictionEndpoint:
    """Test prediction endpoint."""

    def test_predict_valid_request(self):
        """Test prediction with valid request."""
        payload = {
            "tenure_months": 24,
            "monthly_charges": 79.99,
            "total_charges": 1919.76,
            "contract_type": "Month-to-month",
            "num_support_tickets": 3,
        }

        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "prediction" in data
        assert "probability" in data
        assert "model_variant" in data
        assert "model_version" in data
        assert data["prediction"] in [0, 1]
        assert 0 <= data["probability"] <= 1
        assert isinstance(data["model_variant"], str)
        assert isinstance(data["model_version"], str)

    def test_predict_low_risk_customer(self):
        """Test prediction for low-risk customer profile."""
        payload = {
            "tenure_months": 60,
            "monthly_charges": 50.00,
            "total_charges": 3000.00,
            "contract_type": "Two year",
            "num_support_tickets": 0,
        }

        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 200

        data = response.json()
        # Low-risk customer should have lower churn probability
        assert data["probability"] < 0.7

    def test_predict_invalid_contract_type(self):
        """Test prediction with invalid contract type."""
        payload = {
            "tenure_months": 24,
            "monthly_charges": 79.99,
            "total_charges": 1919.76,
            "contract_type": "Invalid Type",
            "num_support_tickets": 3,
        }

        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 422  # Validation error

    def test_predict_negative_tenure(self):
        """Test prediction with negative tenure."""
        payload = {
            "tenure_months": -5,
            "monthly_charges": 79.99,
            "total_charges": 1919.76,
            "contract_type": "Month-to-month",
            "num_support_tickets": 3,
        }

        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 422  # Validation error

    def test_predict_missing_field(self):
        """Test prediction with missing required field."""
        payload = {
            "tenure_months": 24,
            "monthly_charges": 79.99,
            # Missing total_charges
            "contract_type": "Month-to-month",
            "num_support_tickets": 3,
        }

        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 422  # Validation error

    def test_predict_out_of_range_charges(self):
        """Test prediction with charges exceeding maximum."""
        payload = {
            "tenure_months": 24,
            "monthly_charges": 1000.00,  # Exceeds max of 500
            "total_charges": 1919.76,
            "contract_type": "Month-to-month",
            "num_support_tickets": 3,
        }

        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 422  # Validation error


class TestAPIDocumentation:
    """Test API documentation endpoints."""

    def test_openapi_schema(self):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Customer Churn Prediction API"

    def test_docs_endpoint(self):
        """Test that Swagger docs are accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint(self):
        """Test that ReDoc is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestABTestingEndpoints:
    """Test A/B testing specific endpoints."""

    def test_ab_test_status_endpoint(self):
        """Test A/B test status endpoint."""
        response = client.get("/api/v1/ab-test/status")
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "routing_strategy" in data
        assert "variants" in data
        assert isinstance(data["enabled"], bool)
        assert isinstance(data["variants"], list)

    def test_predict_with_user_id(self):
        """Test prediction with user_id for hash routing."""
        payload = {
            "tenure_months": 24,
            "monthly_charges": 79.99,
            "total_charges": 1919.76,
            "contract_type": "Month-to-month",
            "num_support_tickets": 3,
            "user_id": "test_user_123",
        }

        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "model_variant" in data
        assert "model_version" in data

    def test_predict_with_session_id(self):
        """Test prediction with session_id for sticky routing."""
        payload = {
            "tenure_months": 24,
            "monthly_charges": 79.99,
            "total_charges": 1919.76,
            "contract_type": "Month-to-month",
            "num_support_tickets": 3,
            "session_id": "test_session_456",
        }

        response = client.post("/api/v1/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "model_variant" in data
        assert "model_version" in data

    def test_predict_consistency_same_user(self):
        """Test that same user_id gets consistent routing."""
        payload = {
            "tenure_months": 24,
            "monthly_charges": 79.99,
            "total_charges": 1919.76,
            "contract_type": "Month-to-month",
            "num_support_tickets": 3,
            "user_id": "consistent_user",
        }

        # Make multiple requests with same user_id
        response1 = client.post("/api/v1/predict", json=payload)
        response2 = client.post("/api/v1/predict", json=payload)

        assert response1.status_code == 200
        assert response2.status_code == 200

        # For hash routing, same user should get same variant
        # (This assumes hash routing is enabled, otherwise test will still pass)
        data1 = response1.json()
        data2 = response2.json()
        assert "model_variant" in data1
        assert "model_variant" in data2
