"""
Feast Feature Store Repository Configuration.

This module defines the feature store setup for the churn prediction platform,
including data sources, feature views, and feature services.
"""

from datetime import timedelta

from feast import Entity, Feature, FeatureView, FileSource, ValueType
from feast.data_source import RequestSource
from feast.feature_service import FeatureService
from feast.on_demand_feature_view import on_demand_feature_view
from feast.types import Float32, Int32, String

# Define Customer entity
customer = Entity(
    name="customer_id",
    description="Customer identifier",
    value_type=ValueType.STRING,
)

# Data source for customer churn features
customer_features_source = FileSource(
    path="data/customer_features.parquet",
    timestamp_field="event_timestamp",
)

# Feature view for customer behavior features
customer_behavior_features = FeatureView(
    name="customer_behavior_features",
    entities=["customer_id"],
    ttl=timedelta(days=1),
    features=[
        Feature(name="tenure_months", dtype=ValueType.INT32),
        Feature(name="monthly_charges", dtype=ValueType.FLOAT),
        Feature(name="total_charges", dtype=ValueType.FLOAT),
        Feature(name="num_support_tickets", dtype=ValueType.INT32),
    ],
    online=True,
    source=customer_features_source,
    tags={"team": "ml-platform", "use_case": "churn_prediction"},
)

# Feature view for customer demographics
customer_demographics_source = FileSource(
    path="data/customer_demographics.parquet",
    timestamp_field="event_timestamp",
)

customer_demographics_features = FeatureView(
    name="customer_demographics_features",
    entities=["customer_id"],
    ttl=timedelta(days=7),
    features=[
        Feature(name="age", dtype=ValueType.INT32),
        Feature(name="gender", dtype=ValueType.STRING),
        Feature(name="location", dtype=ValueType.STRING),
    ],
    online=True,
    source=customer_demographics_source,
    tags={"team": "ml-platform", "use_case": "churn_prediction"},
)

# Feature view for contract information
customer_contract_source = FileSource(
    path="data/customer_contract.parquet",
    timestamp_field="event_timestamp",
)

customer_contract_features = FeatureView(
    name="customer_contract_features",
    entities=["customer_id"],
    ttl=timedelta(days=1),
    features=[
        Feature(name="contract_type", dtype=ValueType.STRING),
        Feature(name="payment_method", dtype=ValueType.STRING),
        Feature(name="paperless_billing", dtype=ValueType.INT32),
    ],
    online=True,
    source=customer_contract_source,
    tags={"team": "ml-platform", "use_case": "churn_prediction"},
)

# Request data source for on-demand features
request_source = RequestSource(
    name="request_data",
    schema=[
        Feature(name="monthly_charges", dtype=ValueType.FLOAT),
        Feature(name="tenure_months", dtype=ValueType.INT32),
    ],
)


# On-demand feature view for derived features
@on_demand_feature_view(
    sources=[request_source, customer_behavior_features],
    schema=[
        Feature(name="charges_per_month_ratio", dtype=ValueType.FLOAT),
        Feature(name="avg_charges_per_tenure", dtype=ValueType.FLOAT),
    ],
)
def customer_derived_features(inputs: dict) -> dict:
    """Calculate derived features on-demand."""
    output = {}

    # Charges per month ratio (current vs average)
    if inputs["monthly_charges"] and inputs["total_charges"]:
        total_charges = inputs["total_charges"]
        monthly_charges = inputs["monthly_charges"]
        tenure_months = max(inputs["tenure_months"], 1)
        avg_monthly = total_charges / tenure_months

        output["charges_per_month_ratio"] = (
            monthly_charges / avg_monthly if avg_monthly > 0 else 1.0
        )
        output["avg_charges_per_tenure"] = avg_monthly
    else:
        output["charges_per_month_ratio"] = 1.0
        output["avg_charges_per_tenure"] = 0.0

    return output


# Feature service for churn prediction model
churn_prediction_service = FeatureService(
    name="churn_prediction_v1",
    features=[
        customer_behavior_features,
        customer_contract_features,
        customer_derived_features,
    ],
    tags={"model": "churn_classifier", "version": "v1"},
)

# Feature service for real-time predictions
churn_prediction_online_service = FeatureService(
    name="churn_prediction_online",
    features=[
        customer_behavior_features[["tenure_months", "monthly_charges", "num_support_tickets"]],
        customer_contract_features[["contract_type"]],
    ],
    tags={"serving": "online", "latency": "low"},
)
