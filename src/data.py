"""Generate synthetic customer churn data."""

import numpy as np
import pandas as pd


def generate_churn_data(n_samples=1000, random_state=42):
    """
    Generate synthetic customer churn data.

    Args:
        n_samples: Number of samples to generate
        random_state: Random seed for reproducibility

    Returns:
        DataFrame with customer features and churn label
    """
    np.random.seed(random_state)

    data = {
        "tenure_months": np.random.randint(1, 72, n_samples),
        "monthly_charges": np.random.uniform(20, 120, n_samples),
        "total_charges": np.random.uniform(100, 8000, n_samples),
        "contract_type": np.random.choice(
            ["Month-to-month", "One year", "Two year"], n_samples
        ),
        "num_support_tickets": np.random.poisson(2, n_samples),
    }

    df = pd.DataFrame(data)

    # Generate churn based on features
    churn_prob = (
        (df["tenure_months"] < 12) * 0.3
        + (df["contract_type"] == "Month-to-month") * 0.3
        + (df["monthly_charges"] > 80) * 0.2
    )
    df["churn"] = (np.random.random(n_samples) < churn_prob).astype(int)

    return df
