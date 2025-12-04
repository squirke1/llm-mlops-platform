"""Train the customer churn prediction model."""

from pathlib import Path

import mlflow.sklearn
import pandas as pd

import mlflow
from data import generate_churn_data
from model import ChurnModel


def main():
    """Train and save the churn prediction model."""
    import os

    # Check if MLflow should be used
    use_mlflow = os.getenv("USE_MLFLOW", "false").lower() == "true"

    if use_mlflow:
        # Set MLflow tracking URI and experiment
        mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
        mlflow.set_tracking_uri(mlflow_uri)
        mlflow.set_experiment("churn-prediction")
        print(f"MLflow tracking enabled: {mlflow_uri}")
        mlflow.start_run(run_name="churn-model-training")
    else:
        print("MLflow tracking disabled (set USE_MLFLOW=true to enable)")
        print("Generating training data...")
        df = generate_churn_data(n_samples=1000, random_state=42)

        # Prepare features and target
        print("Preparing features...")
        # One-hot encode categorical features
        df_encoded = pd.get_dummies(df, columns=["contract_type"], drop_first=True)

        X = df_encoded.drop("churn", axis=1)
        y = df_encoded["churn"]

        # Log parameters
        n_estimators = 100
        random_state = 42
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("random_state", random_state)
        mlflow.log_param("n_samples", len(df))
        mlflow.log_param("n_features", X.shape[1])

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
