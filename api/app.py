"""FastAPI application for churn prediction."""

import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.ab_testing import (  # noqa: E402
    ab_test_manager,
    configure_ab_test_from_env,
    variant_errors,
    variant_latency,
    variant_requests,
)
from api.schemas import (  # noqa: E402
    ChurnPredictionRequest,
    ChurnPredictionResponse,
    HealthResponse,
)
from src.mlflow_utils import load_model_from_registry  # noqa: E402
from src.model import ChurnModel  # noqa: E402

# Feature store imports (optional - gracefully handle if not available)
try:
    from feature_store import get_feature_store_client, get_features_for_prediction  # noqa: E402

    FEATURE_STORE_AVAILABLE = True
except ImportError:
    FEATURE_STORE_AVAILABLE = False
    print(
        "Warning: Feature store not available. Install feast to enable feature store integration."
    )

# Initialize FastAPI app
app = FastAPI(
    title="Customer Churn Prediction API",
    description="REST API for predicting customer churn",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model variable
model = None
feature_store_client = None

# Prometheus metrics
prediction_counter = Counter(
    "churn_predictions_total",
    "Total number of churn predictions",
    ["prediction_result"],
)
prediction_latency = Histogram(
    "churn_prediction_duration_seconds",
    "Time spent processing prediction requests",
)
model_confidence = Gauge(
    "churn_model_confidence",
    "Average confidence score of predictions",
)
active_predictions = Gauge(
    "churn_predictions_in_progress",
    "Number of predictions currently being processed",
)


# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.on_event("startup")
async def load_model():
    """Load the trained model(s) on startup and configure A/B testing."""
    global model, feature_store_client

    # Initialize feature store client if available
    if FEATURE_STORE_AVAILABLE:
        try:
            repo_path = Path(__file__).parent.parent / "feature_store"
            if repo_path.exists():
                feature_store_client = get_feature_store_client(str(repo_path))
                print("Feature store client initialized successfully")
            else:
                print(f"Warning: Feature store repository not found at {repo_path}")
        except Exception as e:
            print(f"Warning: Failed to initialize feature store: {e}")

    # Configure A/B testing from environment
    traffic_config = configure_ab_test_from_env()

    # MLflow model wrapper
    class MLflowModelWrapper:
        def __init__(self, mlflow_model):
            self.model = mlflow_model

        def predict(self, X):
            return self.model.predict(X)

    # Try loading production model from MLflow
    print("Attempting to load production model from MLflow registry...")
    production_model = load_model_from_registry(
        model_name="churn-prediction-model", stage="Production"
    )

    if production_model is not None:
        model = MLflowModelWrapper(production_model)
        print("Production model loaded from MLflow registry")

        # Add as primary variant for A/B testing
        ab_test_manager.add_variant(
            name="production",
            model=model,
            traffic_percentage=100,
            version="production",
            stage="champion",
        )

        # Try loading staging model for A/B testing
        staging_model = load_model_from_registry(
            model_name="churn-prediction-model", stage="Staging"
        )

        if staging_model is not None:
            staging_wrapped = MLflowModelWrapper(staging_model)
            print("Staging model loaded from MLflow registry")

            # Configure A/B test if traffic config provided
            if traffic_config:
                prod_traffic = traffic_config.get("production", 90)
                staging_traffic = traffic_config.get("staging", 10)

                ab_test_manager.update_traffic_split(
                    {"production": prod_traffic, "staging": staging_traffic}
                )
                ab_test_manager.add_variant(
                    name="staging",
                    model=staging_wrapped,
                    traffic_percentage=staging_traffic,
                    version="staging",
                    stage="challenger",
                )
                ab_test_manager.enable_test("production_vs_staging")
                print(f"A/B test enabled: production={prod_traffic}%, staging={staging_traffic}%")
    else:
        # Fallback to local file
        print("Falling back to local model file...")
        model_path = Path("models/churn_model.pkl")

        if not model_path.exists():
            print(f"Warning: Model file not found at {model_path}")
            print("Please train the model first by running: python src/train.py")
            model = None
        else:
            try:
                model = ChurnModel.load(model_path)
                print(f"Model loaded successfully from {model_path}")

                # Add as single variant
                ab_test_manager.add_variant(
                    name="local",
                    model=model,
                    traffic_percentage=100,
                    version="local",
                    stage="champion",
                )
            except Exception as e:
                print(f"Error loading model: {e}")
                model = None


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {"message": "Customer Churn Prediction API", "docs": "/docs", "health": "/health"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        version="1.0.0",
        ab_testing_enabled=ab_test_manager.is_test_active(),
        feature_store_available=feature_store_client is not None,
    )


@app.get("/api/v1/ab-test/status", tags=["A/B Testing"])
async def get_ab_test_status():
    """Get current A/B test configuration and statistics."""
    return ab_test_manager.get_variant_stats()


@app.get("/api/v1/features/health", tags=["Feature Store"])
async def feature_store_health():
    """Check feature store health and availability."""
    from api.schemas import FeatureStoreHealthResponse

    if not FEATURE_STORE_AVAILABLE:
        return FeatureStoreHealthResponse(
            available=False, error="Feature store package not installed"
        )

    if feature_store_client is None:
        return FeatureStoreHealthResponse(
            available=False, error="Feature store client not initialized"
        )

    try:
        # Test online store connectivity
        feature_views = feature_store_client.list_feature_views()
        feature_services = feature_store_client.list_feature_services()

        # Try to validate with a test entity
        test_entity = [{"customer_id": "test_customer"}]
        is_healthy = feature_store_client.validate_features(test_entity)

        return FeatureStoreHealthResponse(
            available=True,
            online_store_healthy=is_healthy,
            feature_views_count=len(feature_views),
            feature_services_count=len(feature_services),
        )
    except Exception as e:
        return FeatureStoreHealthResponse(available=True, online_store_healthy=False, error=str(e))


@app.post("/api/v1/predict/features", response_model=ChurnPredictionResponse, tags=["Prediction"])
async def predict_churn_with_features(
    customer_id: str, user_id: Optional[str] = None, session_id: Optional[str] = None
):
    """
    Predict customer churn using features from feature store.

    This endpoint retrieves features for the given customer_id from the
    feature store and makes a prediction using the loaded model.

    Args:
        customer_id: Customer ID for feature retrieval
        user_id: Optional user identifier for hash-based A/B routing
        session_id: Optional session identifier for sticky A/B routing

    Returns:
        ChurnPredictionResponse with prediction, probability, and variant info

    Raises:
        HTTPException: If model not loaded, feature store unavailable, or prediction fails
    """
    if model is None:
        raise HTTPException(
            status_code=503, detail="Model not loaded. Please train the model first."
        )

    if not FEATURE_STORE_AVAILABLE or feature_store_client is None:
        raise HTTPException(
            status_code=503,
            detail="Feature store not available. Use /api/v1/predict endpoint instead.",
        )

    # Select model variant for A/B testing
    variant = ab_test_manager.select_variant(user_id=user_id, session_id=session_id)
    selected_model = variant.model if variant else model
    variant_name = variant.name if variant else "default"
    variant_version = variant.version if variant else "unknown"

    # Track prediction in progress
    active_predictions.inc()

    try:
        import time

        start_time = time.time()

        # Track variant metrics
        if variant:
            variant_requests.labels(
                variant_name=variant_name, variant_version=variant_version
            ).inc()

        # Get features from feature store
        features = get_features_for_prediction(customer_id, feature_store_client)

        if not features:
            raise HTTPException(
                status_code=404, detail=f"Features not found for customer_id: {customer_id}"
            )

        # Prepare input data from feature store features
        input_data = pd.DataFrame(
            [
                {
                    "tenure_months": features.get("tenure_months", 0),
                    "monthly_charges": features.get("monthly_charges", 0.0),
                    "total_charges": features.get("total_charges", 0.0),
                    "num_support_tickets": features.get("num_support_tickets", 0),
                    "contract_type": features.get("contract_type", "Month-to-month"),
                }
            ]
        )

        # Encode contract type (one-hot encoding matching training)
        input_encoded = pd.get_dummies(input_data, columns=["contract_type"], drop_first=True)

        # Ensure all columns from training are present
        expected_cols = [
            "tenure_months",
            "monthly_charges",
            "total_charges",
            "num_support_tickets",
            "contract_type_One year",
            "contract_type_Two year",
        ]

        for col in expected_cols:
            if col not in input_encoded.columns:
                input_encoded[col] = 0

        # Reorder columns to match training data
        input_encoded = input_encoded[expected_cols]

        # Make prediction
        prediction = selected_model.predict(input_encoded)[0]

        # Get probability (use predict_proba if available)
        if hasattr(selected_model.model, "predict_proba"):
            probability = float(selected_model.model.predict_proba(input_encoded)[0][1])
        else:
            probability = float(prediction)

        # Record metrics
        duration = time.time() - start_time
        prediction_latency.observe(duration)
        prediction_label = "churn" if prediction == 1 else "no_churn"
        prediction_counter.labels(prediction_result=prediction_label).inc()
        model_confidence.set(probability)
        active_predictions.dec()

        # Track variant-specific metrics
        if variant:
            variant_latency.labels(
                variant_name=variant_name, variant_version=variant_version
            ).observe(duration)

        return ChurnPredictionResponse(
            prediction=int(prediction),
            probability=round(probability, 3),
            model_variant=variant_name,
            model_version=variant_version,
        )

    except HTTPException:
        active_predictions.dec()
        raise
    except Exception as e:
        active_predictions.dec()

        # Track variant-specific errors
        if variant:
            variant_errors.labels(variant_name=variant_name, variant_version=variant_version).inc()

        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/api/v1/predict", response_model=ChurnPredictionResponse, tags=["Prediction"])
async def predict_churn(
    request: ChurnPredictionRequest, user_id: Optional[str] = None, session_id: Optional[str] = None
):
    """
    Predict customer churn probability.

    Args:
        request: ChurnPredictionRequest with customer features
        user_id: Optional user identifier for hash-based A/B routing
        session_id: Optional session identifier for sticky A/B routing

    Returns:
        ChurnPredictionResponse with prediction, probability, and variant info
    """
    if model is None:
        raise HTTPException(
            status_code=503, detail="Model not loaded. Please train the model first."
        )

    # Select model variant for A/B testing
    variant = ab_test_manager.select_variant(user_id=user_id, session_id=session_id)
    selected_model = variant.model if variant else model
    variant_name = variant.name if variant else "default"
    variant_version = variant.version if variant else "unknown"

    # Track prediction in progress
    active_predictions.inc()

    try:
        # Start timing
        import time

        start_time = time.time()

        # Track variant metrics
        if variant:
            variant_requests.labels(
                variant_name=variant_name, variant_version=variant_version
            ).inc()

        # Prepare input data
        input_data = pd.DataFrame(
            [
                {
                    "tenure_months": request.tenure_months,
                    "monthly_charges": request.monthly_charges,
                    "total_charges": request.total_charges,
                    "contract_type": request.contract_type,
                    "num_support_tickets": request.num_support_tickets,
                }
            ]
        )

        # Encode contract type (one-hot encoding matching training)
        input_encoded = pd.get_dummies(input_data, columns=["contract_type"], drop_first=True)

        # Ensure all columns from training are present
        expected_cols = [
            "tenure_months",
            "monthly_charges",
            "total_charges",
            "num_support_tickets",
            "contract_type_One year",
            "contract_type_Two year",
        ]

        for col in expected_cols:
            if col not in input_encoded.columns:
                input_encoded[col] = 0

        # Reorder columns to match training data
        input_encoded = input_encoded[expected_cols]

        # Make prediction
        prediction = selected_model.predict(input_encoded)[0]

        # Get probability (use predict_proba if available)
        if hasattr(selected_model.model, "predict_proba"):
            probability = float(selected_model.model.predict_proba(input_encoded)[0][1])
        else:
            probability = float(prediction)

        # Record metrics
        duration = time.time() - start_time
        prediction_latency.observe(duration)
        prediction_label = "churn" if prediction == 1 else "no_churn"
        prediction_counter.labels(prediction_result=prediction_label).inc()
        model_confidence.set(probability)
        active_predictions.dec()

        # Track variant-specific metrics
        if variant:
            variant_latency.labels(
                variant_name=variant_name, variant_version=variant_version
            ).observe(duration)

        return ChurnPredictionResponse(
            prediction=int(prediction),
            probability=round(probability, 3),
            model_variant=variant_name,
            model_version=variant_version,
        )

    except Exception as e:
        active_predictions.dec()

        # Track variant-specific errors
        if variant:
            variant_errors.labels(variant_name=variant_name, variant_version=variant_version).inc()

        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
