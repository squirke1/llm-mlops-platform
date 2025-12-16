"""Train the customer churn prediction model."""

import os
from datetime import datetime
from pathlib import Path

import mlflow.sklearn
import pandas as pd

import mlflow
from data import generate_churn_data
from model import ChurnModel

# Try to import feature store (optional)
try:
    from feature_store import get_training_features

    FEATURE_STORE_AVAILABLE = True
except ImportError:
    FEATURE_STORE_AVAILABLE = False
    print("Note: Feature store not available. Using generated data.")


def load_data_from_feature_store():
    """Load training data from feature store."""
    if not FEATURE_STORE_AVAILABLE:
        raise RuntimeError("Feature store not available. Install feast package.")

    # Check if feature store is set up
    repo_path = Path("feature_store")
    if not repo_path.exists():
        raise RuntimeError("Feature store repository not found")

    registry_path = Path("data/registry.db")
    if not registry_path.exists():
        raise RuntimeError(
            "Feature store not initialized. Run: python feature_store/setup_feature_store.py"
        )

    print("Loading training data from feature store...")

    # Load customer IDs from feature data
    data_path = Path("data/customer_features.parquet")
    if not data_path.exists():
        raise RuntimeError("Feature data not found. Run: python feature_store/generate_features.py")

    customer_df = pd.read_parquet(data_path)

    # Create entity dataframe with customer IDs and timestamps
    entity_df = pd.DataFrame(
        {
            "customer_id": customer_df["customer_id"].tolist(),
            "event_timestamp": [datetime.now()] * len(customer_df),
        }
    )

    # Get features from feature store
    features_df = get_training_features(entity_df, feature_service="churn_prediction_v1")

    print(f"Loaded {len(features_df)} samples from feature store")
    print(f"Features: {features_df.columns.tolist()}")

    return features_df


def main():
    """Train and save the churn prediction model."""
    # Check if MLflow should be used
    use_mlflow = os.getenv("USE_MLFLOW", "false").lower() == "true"

    # Check if feature store should be used
    use_feature_store = os.getenv("USE_FEATURE_STORE", "false").lower() == "true"

    if use_mlflow:
        # Set MLflow tracking URI and experiment
        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
        mlflow.set_tracking_uri(mlflow_uri)
        mlflow.set_experiment("churn-prediction")
        print(f"MLflow tracking enabled: {mlflow_uri}")
        mlflow.start_run(run_name="churn-model-training")
    else:
        print("MLflow tracking disabled (set USE_MLFLOW=true to enable)")

    # Load training data
    if use_feature_store and FEATURE_STORE_AVAILABLE:
        print("\n=== Using Feature Store for Training Data ===")
        try:
            df = load_data_from_feature_store()
            # Feature store data already includes feature engineering
            # Remove customer_id and event_timestamp for training
            df_encoded = df.drop(["customer_id", "event_timestamp"], axis=1, errors="ignore")
            data_source = "feature_store"
        except Exception as e:
            print(f"Error loading from feature store: {e}")
            print("Falling back to generated data...")
            df = generate_churn_data(n_samples=1000, random_state=42)
            df_encoded = pd.get_dummies(df, columns=["contract_type"], drop_first=True)
            data_source = "generated"
    else:
        print("\n=== Using Generated Training Data ===")
        if use_feature_store and not FEATURE_STORE_AVAILABLE:
            print("Warning: Feature store requested but not available")

        df = generate_churn_data(n_samples=1000, random_state=42)
        df_encoded = pd.get_dummies(df, columns=["contract_type"], drop_first=True)
        data_source = "generated"

    # Prepare features and target
    print("Preparing features...")

    # Check if churn column exists (may not be in feature store)
    if "churn" not in df_encoded.columns:
        # Generate synthetic churn labels for demo
        # In production, these would come from a labeled dataset
        import numpy as np

        np.random.seed(42)
        df_encoded["churn"] = np.random.binomial(1, 0.3, len(df_encoded))
        print("Warning: Generated synthetic churn labels for demonstration")

    X = df_encoded.drop("churn", axis=1)
    y = df_encoded["churn"]

    # Log parameters
    n_estimators = 100
    random_state = 42

    if use_mlflow:
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("random_state", random_state)
        mlflow.log_param("n_samples", len(df))
        mlflow.log_param("n_features", X.shape[1])
        mlflow.log_param("data_source", data_source)
        mlflow.log_param("use_feature_store", use_feature_store)

    # Train model
    print("Training model...")
    model = ChurnModel(n_estimators=n_estimators, random_state=random_state)
    metrics = model.train(X, y)

    # Log metrics to MLflow if enabled
    if use_mlflow:
        mlflow.log_metric("accuracy", metrics["accuracy"])
        mlflow.log_metric("precision", metrics["precision"])
        mlflow.log_metric("recall", metrics["recall"])

    # Print metrics
    print("\nModel Performance:")
    print(f"  Accuracy:  {metrics['accuracy']:.3f}")
    print(f"  Precision: {metrics['precision']:.3f}")
    print(f"  Recall:    {metrics['recall']:.3f}")

    # Save model locally
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    model_path = models_dir / "churn_model.pkl"
    model.save(model_path)
    print(f"\nModel saved to {model_path}")

    # Log model to MLflow if enabled
    if use_mlflow:
        mlflow.sklearn.log_model(
            model.model,
            "model",
            registered_model_name="churn-prediction-model",
            signature=mlflow.models.infer_signature(X, model.predict(X)),
        )
        mlflow.log_artifact(str(model_path), "model-files")
        print(f"\nMLflow run ID: {mlflow.active_run().info.run_id}")
        mlflow.end_run()
    else:
        print("\nModel training complete (MLflow tracking disabled)")


if __name__ == "__main__":
    main()
