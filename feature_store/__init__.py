"""Feature Store package initialization."""

from feature_store.feature_store_client import (
    FeatureStoreClient,
    get_feature_store_client,
    get_features_for_prediction,
    get_training_features,
)

__all__ = [
    "FeatureStoreClient",
    "get_feature_store_client",
    "get_features_for_prediction",
    "get_training_features",
]
