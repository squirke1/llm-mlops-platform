"""
Generate sample feature data for the feature store.

This script creates synthetic customer feature data and saves it in parquet format
for use with the Feast feature store.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def generate_customer_features(n_customers: int = 1000) -> pd.DataFrame:
    """Generate customer behavioral features."""
    np.random.seed(42)

    data = {
        "customer_id": [f"CUST_{i:06d}" for i in range(n_customers)],
        "tenure_months": np.random.randint(1, 72, n_customers),
        "monthly_charges": np.random.uniform(20, 150, n_customers),
        "total_charges": np.random.uniform(100, 8000, n_customers),
        "num_support_tickets": np.random.poisson(2, n_customers),
        "event_timestamp": [
            datetime.now() - timedelta(hours=np.random.randint(0, 168)) for _ in range(n_customers)
        ],
        "created_timestamp": [datetime.now() for _ in range(n_customers)],
    }

    return pd.DataFrame(data)


def generate_customer_demographics(n_customers: int = 1000) -> pd.DataFrame:
    """Generate customer demographic features."""
    np.random.seed(43)

    data = {
        "customer_id": [f"CUST_{i:06d}" for i in range(n_customers)],
        "age": np.random.randint(18, 80, n_customers),
        "gender": np.random.choice(["Male", "Female", "Other"], n_customers),
        "location": np.random.choice(
            ["Urban", "Suburban", "Rural"], n_customers, p=[0.5, 0.3, 0.2]
        ),
        "event_timestamp": [
            datetime.now() - timedelta(hours=np.random.randint(0, 168)) for _ in range(n_customers)
        ],
        "created_timestamp": [datetime.now() for _ in range(n_customers)],
    }

    return pd.DataFrame(data)


def generate_customer_contract(n_customers: int = 1000) -> pd.DataFrame:
    """Generate customer contract features."""
    np.random.seed(44)

    contract_types = ["Month-to-month", "One year", "Two year"]
    payment_methods = ["Electronic check", "Mailed check", "Bank transfer", "Credit card"]

    data = {
        "customer_id": [f"CUST_{i:06d}" for i in range(n_customers)],
        "contract_type": np.random.choice(contract_types, n_customers),
        "payment_method": np.random.choice(payment_methods, n_customers),
        "paperless_billing": np.random.randint(0, 2, n_customers),
        "event_timestamp": [
            datetime.now() - timedelta(hours=np.random.randint(0, 168)) for _ in range(n_customers)
        ],
        "created_timestamp": [datetime.now() for _ in range(n_customers)],
    }

    return pd.DataFrame(data)


def save_features_to_parquet(data_dir: str = "data"):
    """Generate and save all feature data to parquet files."""
    # Create data directory if it doesn't exist
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    print("Generating customer features...")
    customer_features = generate_customer_features()
    customer_features_path = os.path.join(data_dir, "customer_features.parquet")
    customer_features.to_parquet(customer_features_path, index=False)
    print(f"Saved customer features to {customer_features_path}")

    print("Generating customer demographics...")
    demographics = generate_customer_demographics()
    demographics_path = os.path.join(data_dir, "customer_demographics.parquet")
    demographics.to_parquet(demographics_path, index=False)
    print(f"Saved demographics to {demographics_path}")

    print("Generating customer contract data...")
    contract_data = generate_customer_contract()
    contract_path = os.path.join(data_dir, "customer_contract.parquet")
    contract_data.to_parquet(contract_path, index=False)
    print(f"Saved contract data to {contract_path}")

    print("\nFeature data generation complete!")
    print(f"Total customers: {len(customer_features)}")


if __name__ == "__main__":
    save_features_to_parquet()
