"""
Feature Store utilities for serving features online and offline.

This module provides helper functions for interacting with the Feast feature store,
including feature retrieval, materialization, and validation.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from feast import FeatureStore


class FeatureStoreClient:
    """Client for interacting with the Feast feature store."""

    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize the feature store client.

        Args:
            repo_path: Path to the feature repository. Defaults to ./feature_store
        """
        if repo_path is None:
            repo_path = str(Path(__file__).parent)

        self.repo_path = repo_path
        self.store = FeatureStore(repo_path=repo_path)
        print(f"Initialized Feature Store from {repo_path}")

    def get_online_features(
        self,
        feature_service: str,
        entity_rows: List[Dict[str, Any]],
    ) -> pd.DataFrame:
        """
        Retrieve features from the online store for real-time serving.

        Args:
            feature_service: Name of the feature service to use
            entity_rows: List of entity dictionaries (e.g., [{"customer_id": "123"}])

        Returns:
            DataFrame with requested features
        """
        try:
            # Get features from online store
            feature_vector = self.store.get_online_features(
                features=self.store.get_feature_service(feature_service),
                entity_rows=entity_rows,
            )

            # Convert to DataFrame
            df = feature_vector.to_df()
            return df

        except Exception as e:
            print(f"Error retrieving online features: {e}")
            raise

    def get_historical_features(
        self,
        entity_df: pd.DataFrame,
        features: List[str],
    ) -> pd.DataFrame:
        """
        Retrieve historical features for training.

        Args:
            entity_df: DataFrame with entity keys and timestamps
            features: List of feature references (e.g., ["customer_behavior_features:tenure_months"])

        Returns:
            DataFrame with requested historical features
        """
        try:
            training_df = self.store.get_historical_features(
                entity_df=entity_df,
                features=features,
            ).to_df()

            return training_df

        except Exception as e:
            print(f"Error retrieving historical features: {e}")
            raise

    def materialize_features(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):
        """
        Materialize features to the online store.

        Args:
            start_date: Start date for materialization. Defaults to 7 days ago.
            end_date: End date for materialization. Defaults to now.
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()

        try:
            print(f"Materializing features from {start_date} to {end_date}")
            self.store.materialize(
                start_date=start_date,
                end_date=end_date,
            )
            print("Materialization complete")

        except Exception as e:
            print(f"Error materializing features: {e}")
            raise

    def get_feature_service_features(self, service_name: str) -> List[str]:
        """
        Get list of features in a feature service.

        Args:
            service_name: Name of the feature service

        Returns:
            List of feature names
        """
        try:
            service = self.store.get_feature_service(service_name)
            features = []
            for feature_view_projection in service.feature_view_projections:
                view_name = feature_view_projection.name
                for feature in feature_view_projection.features:
                    features.append(f"{view_name}:{feature.name}")
            return features

        except Exception as e:
            print(f"Error getting feature service features: {e}")
            raise

    def list_feature_views(self) -> List[str]:
        """List all feature views in the registry."""
        try:
            feature_views = self.store.list_feature_views()
            return [fv.name for fv in feature_views]

        except Exception as e:
            print(f"Error listing feature views: {e}")
            raise

    def list_feature_services(self) -> List[str]:
        """List all feature services in the registry."""
        try:
            feature_services = self.store.list_feature_services()
            return [fs.name for fs in feature_services]

        except Exception as e:
            print(f"Error listing feature services: {e}")
            raise

    def validate_features(self, entity_rows: List[Dict[str, Any]]) -> bool:
        """
        Validate that features can be retrieved for given entities.

        Args:
            entity_rows: List of entity dictionaries

        Returns:
            True if features can be retrieved, False otherwise
        """
        try:
            # Try to get online features for first available service
            services = self.list_feature_services()
            if not services:
                print("No feature services found")
                return False

            service_name = services[0]
            df = self.get_online_features(service_name, entity_rows)

            # Check if we got data back
            return len(df) > 0 and not df.empty

        except Exception as e:
            print(f"Feature validation failed: {e}")
            return False


# Singleton instance
_feature_store_client: Optional[FeatureStoreClient] = None


def get_feature_store_client(repo_path: Optional[str] = None) -> FeatureStoreClient:
    """
    Get or create the feature store client singleton.

    Args:
        repo_path: Path to the feature repository

    Returns:
        FeatureStoreClient instance
    """
    global _feature_store_client

    if _feature_store_client is None:
        _feature_store_client = FeatureStoreClient(repo_path=repo_path)

    return _feature_store_client


def get_features_for_prediction(customer_id: str) -> Dict[str, Any]:
    """
    Get features for a single customer prediction.

    Args:
        customer_id: Customer identifier

    Returns:
        Dictionary of features
    """
    client = get_feature_store_client()

    # Get online features for prediction
    entity_rows = [{"customer_id": customer_id}]

    try:
        # Use the online prediction service
        df = client.get_online_features(
            feature_service="churn_prediction_online",
            entity_rows=entity_rows,
        )

        # Convert to dictionary
        if len(df) > 0:
            features = df.iloc[0].to_dict()
            # Remove the customer_id from features
            features.pop("customer_id", None)
            return features
        else:
            return {}

    except Exception as e:
        print(f"Error getting features for customer {customer_id}: {e}")
        return {}


def get_training_features(
    entity_df: pd.DataFrame,
    feature_service: str = "churn_prediction_v1",
) -> pd.DataFrame:
    """
    Get historical features for model training.

    Args:
        entity_df: DataFrame with customer_id and event_timestamp columns
        feature_service: Name of the feature service to use

    Returns:
        DataFrame with features for training
    """
    client = get_feature_store_client()

    # Get features from the service
    features = client.get_feature_service_features(feature_service)

    # Retrieve historical features
    training_df = client.get_historical_features(
        entity_df=entity_df,
        features=features,
    )

    return training_df
