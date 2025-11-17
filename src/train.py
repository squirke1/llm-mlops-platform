"""Train the customer churn prediction model."""

import os
from pathlib import Path

import pandas as pd

from data import generate_churn_data
from model import ChurnModel


def main():
    """Train and save the churn prediction model."""
    print("Generating training data...")
    df = generate_churn_data(n_samples=1000, random_state=42)

    # Prepare features and target
    print("Preparing features...")
    # One-hot encode categorical features
    df_encoded = pd.get_dummies(df, columns=["contract_type"], drop_first=True)

    X = df_encoded.drop("churn", axis=1)
    y = df_encoded["churn"]

    # Train model
    print("Training model...")
    model = ChurnModel(n_estimators=100, random_state=42)
    metrics = model.train(X, y)

    # Print metrics
    print("\nModel Performance:")
    print(f"  Accuracy:  {metrics['accuracy']:.3f}")
    print(f"  Precision: {metrics['precision']:.3f}")
    print(f"  Recall:    {metrics['recall']:.3f}")

    # Save model
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    model_path = models_dir / "churn_model.pkl"
    model.save(model_path)
    print(f"\nModel saved to {model_path}")


if __name__ == "__main__":
    main()
