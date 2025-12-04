"""Utility functions for MLflow integration."""

import os
from typing import Optional

import mlflow.pyfunc
from mlflow.tracking import MlflowClient

import mlflow


def get_mlflow_tracking_uri() -> str:
    """Get MLflow tracking URI from environment or default."""
    return os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-server:5000")


def load_model_from_registry(
    model_name: str = "churn-prediction-model", stage: str = "Production"
) -> Optional[mlflow.pyfunc.PyFuncModel]:
    """
    Load model from MLflow model registry.

    Args:
        model_name: Name of the registered model
        stage: Model stage (None, Staging, Production, Archived)

    Returns:
        Loaded model or None if not found
    """
    try:
        mlflow.set_tracking_uri(get_mlflow_tracking_uri())
        model_uri = f"models:/{model_name}/{stage}"
        model = mlflow.pyfunc.load_model(model_uri)
        print(f"Loaded model from MLflow registry: {model_uri}")
        return model
    except Exception as e:
        print(f"Failed to load model from MLflow registry: {e}")
        return None


def get_latest_model_version(model_name: str = "churn-prediction-model") -> Optional[int]:
    """
    Get the latest version number of a registered model.

    Args:
        model_name: Name of the registered model

    Returns:
        Latest version number or None
    """
    try:
        mlflow.set_tracking_uri(get_mlflow_tracking_uri())
        client = MlflowClient()
        versions = client.search_model_versions(f"name='{model_name}'")
        if versions:
            return max(int(v.version) for v in versions)
        return None
    except Exception as e:
        print(f"Failed to get latest model version: {e}")
        return None


def get_model_info(model_name: str = "churn-prediction-model", stage: str = "Production") -> dict:
    """
    Get information about a registered model.

    Args:
        model_name: Name of the registered model
        stage: Model stage

    Returns:
        Dictionary with model information
    """
    try:
        mlflow.set_tracking_uri(get_mlflow_tracking_uri())
        client = MlflowClient()
        versions = client.search_model_versions(f"name='{model_name}' AND current_stage='{stage}'")
        if versions:
            latest = versions[0]
            run = client.get_run(latest.run_id)
            return {
                "name": model_name,
                "version": latest.version,
                "stage": latest.current_stage,
                "run_id": latest.run_id,
                "metrics": run.data.metrics,
                "params": run.data.params,
                "tags": run.data.tags,
            }
        return {}
    except Exception as e:
        print(f"Failed to get model info: {e}")
        return {}
