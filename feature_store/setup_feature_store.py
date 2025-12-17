"""
Initialize and materialize the Feast feature store.

This script sets up the feature store registry and materializes features
to the online store for serving.
"""

from datetime import datetime, timedelta

from feast import FeatureStore


def initialize_feature_store(repo_path: str = "feature_store"):
    """
    Initialize the feature store by applying the feature repository.

    Args:
        repo_path: Path to the feature repository
    """
    print("Initializing Feast Feature Store...")
    print(f"Repository path: {repo_path}")

    try:
        # Initialize the feature store
        store = FeatureStore(repo_path=repo_path)

        # Apply the feature repository (register features)
        print("\nApplying feature definitions to registry...")
        store.apply([])  # Empty list to apply all features from repo

        print("✓ Feature store initialized successfully")

        # List registered features
        print("\nRegistered Feature Views:")
        feature_views = store.list_feature_views()
        for fv in feature_views:
            print(f"  - {fv.name} ({len(fv.features)} features)")

        print("\nRegistered Feature Services:")
        feature_services = store.list_feature_services()
        for fs in feature_services:
            print(f"  - {fs.name}")

        return store

    except Exception as e:
        print(f"Error initializing feature store: {e}")
        raise


def materialize_features(
    repo_path: str = "feature_store",
    days_back: int = 7,
):
    """
    Materialize features from offline to online store.

    Args:
        repo_path: Path to the feature repository
        days_back: Number of days of historical data to materialize
    """
    print(f"\nMaterializing features from the last {days_back} days...")

    try:
        store = FeatureStore(repo_path=repo_path)

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        print(f"Start date: {start_date}")
        print(f"End date: {end_date}")

        # Materialize to online store
        store.materialize(
            start_date=start_date,
            end_date=end_date,
        )

        print("✓ Features materialized successfully")

        # Verify materialization
        print("\nVerifying online store...")
        try:
            # Test retrieval
            entity_rows = [{"customer_id": "CUST_000001"}]
            services = store.list_feature_services()

            if services:
                service_name = services[0].name
                features = store.get_online_features(
                    features=store.get_feature_service(service_name),
                    entity_rows=entity_rows,
                )
                df = features.to_df()
                print(f"✓ Successfully retrieved {len(df.columns)} features from online store")
            else:
                print("⚠ No feature services found for verification")

        except Exception as e:
            print(f"⚠ Online store verification failed: {e}")

    except Exception as e:
        print(f"Error materializing features: {e}")
        raise


def main():
    """Main execution function."""
    print("=" * 60)
    print("Feast Feature Store Setup")
    print("=" * 60)

    repo_path = "feature_store"

    # Step 1: Initialize feature store
    try:
        initialize_feature_store(repo_path)
    except Exception as e:
        print(f"\nFailed to initialize feature store: {e}")
        print("Please ensure feature data exists in the data/ directory")
        print("Run: python feature_store/generate_features.py")
        import sys
        sys.exit(1)

    # Step 2: Materialize features
    try:
        materialize_features(repo_path, days_back=7)
    except Exception as e:
        print(f"\\nFailed to materialize features: {e}")
        print("Please ensure feature data exists and is properly formatted")
        import sys
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Feature Store setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Integrate with training pipeline: Update src/train.py")
    print("2. Integrate with API: Update api/app.py")
    print("3. Set up materialization schedule for production")


if __name__ == "__main__":
    main()
