# Feature Store Integration Guide

## Overview

The MLOps platform now includes a Feature Store powered by Feast for centralized feature management, ensuring consistency between training and serving, and enabling feature reuse across models.

## Architecture

```
            
  Data Sources     Feast Registry    Online Store   
  (Parquet/S3)            (SQLite/S3)           (SQLite/DynamoDB)
            
                                                            
                                                            
                                                            
                               
                          Training               Serving (API)   
                          Pipeline               Real-time       
                               
```

## Components

### 1. Feature Definitions (`feature_store/feature_repo.py`)

Defines all features, entities, and feature views:

- **Entities**: `customer_id`
- **Feature Views**:
  - `customer_behavior_features`: tenure, charges, support tickets
  - `customer_demographics_features`: age, gender, location
  - `customer_contract_features`: contract type, payment method
  - `customer_derived_features`: On-demand calculated features

- **Feature Services**:
  - `churn_prediction_v1`: All features for model training
  - `churn_prediction_online`: Subset for low-latency serving

### 2. Feature Store Client (`feature_store/feature_store_client.py`)

Provides high-level API for feature retrieval:

```python
from feature_store import get_features_for_prediction, get_training_features

# Get features for online prediction
features = get_features_for_prediction(customer_id="CUST_000123")

# Get features for training
entity_df = pd.DataFrame({
    'customer_id': ['CUST_001', 'CUST_002'],
    'event_timestamp': [datetime.now(), datetime.now()]
})
training_df = get_training_features(entity_df)
```

### 3. Feature Generation (`feature_store/generate_features.py`)

Creates synthetic feature data for development and testing:

```bash
python feature_store/generate_features.py
```

This generates parquet files in the `data/` directory:
- `customer_features.parquet`
- `customer_demographics.parquet`
- `customer_contract.parquet`

### 4. Feature Store Setup (`feature_store/setup_feature_store.py`)

Initializes and materializes the feature store:

```bash
python feature_store/setup_feature_store.py
```

This:
1. Applies feature definitions to the registry
2. Materializes historical features to the online store
3. Verifies feature retrieval

## Configuration

### Local Development (`feature_store/feature_store.yaml`)

```yaml
project: churn_prediction
registry: data/registry.db
provider: local
online_store:
    type: sqlite
    path: data/online_store.db
offline_store:
    type: file
```

### Production (Kubernetes ConfigMap)

```yaml
project: churn_prediction
registry: s3://mlops-feature-store/registry.db
provider: aws
online_store:
    type: dynamodb
    region: us-west-2
offline_store:
    type: file
    path: s3://mlops-feature-store/offline
```

## Usage

### Training Pipeline Integration

```python
from feature_store import get_training_features
import pandas as pd
from datetime import datetime

# Prepare entity DataFrame with customer IDs and timestamps
entity_df = pd.DataFrame({
    'customer_id': customer_ids,
    'event_timestamp': [datetime.now()] * len(customer_ids)
})

# Retrieve historical features
features_df = get_training_features(
    entity_df=entity_df,
    feature_service="churn_prediction_v1"
)

# Train model with features
X = features_df.drop(['customer_id', 'event_timestamp', 'churn'], axis=1)
y = features_df['churn']
model.fit(X, y)
```

### API Integration

```python
from feature_store import get_features_for_prediction

@app.post("/api/v1/predict")
async def predict_churn(customer_id: str):
    # Get features from feature store
    features = get_features_for_prediction(customer_id)
    
    # Make prediction
    prediction = model.predict([list(features.values())])
    
    return {"prediction": int(prediction[0])}
```

### Feature Materialization Schedule

Features are automatically materialized every 6 hours via Kubernetes CronJob:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: feature-store-materialization
spec:
  schedule: "0 */6 * * *"
```

## Feature Discovery

List available features:

```python
from feature_store import get_feature_store_client

client = get_feature_store_client()

# List all feature views
feature_views = client.list_feature_views()
print("Feature Views:", feature_views)

# List all feature services
services = client.list_feature_services()
print("Feature Services:", services)

# Get features in a service
features = client.get_feature_service_features("churn_prediction_v1")
print("Features:", features)
```

## Monitoring

### Feature Freshness

Monitor feature freshness in Prometheus:

```promql
# Time since last materialization
time() - feast_materialization_last_success_timestamp

# Feature retrieval latency
feast_feature_retrieval_duration_seconds
```

### Feature Quality

Track feature statistics:
- Missing value rates
- Feature distributions
- Drift detection

## Best Practices

### 1. Feature Naming Convention

```
<domain>_<feature_name>
Example: customer_tenure_months, contract_type
```

### 2. Feature TTL

Set appropriate TTL based on feature update frequency:
- Real-time features: `ttl=timedelta(hours=1)`
- Daily features: `ttl=timedelta(days=1)`
- Static features: `ttl=timedelta(days=365)`

### 3. Materialization Strategy

- **Online store**: Critical for low-latency serving
- **Offline store**: Provides historical features for training
- **Incremental materialization**: Only materialize new data

### 4. Feature Versioning

Tag features with versions:

```python
tags={"version": "v2", "owner": "ml-team"}
```

### 5. Testing

Always test feature retrieval before deployment:

```python
# Validate features can be retrieved
entity_rows = [{"customer_id": "test_customer"}]
is_valid = client.validate_features(entity_rows)
assert is_valid, "Feature validation failed"
```

## Deployment

### Prerequisites

1. Install Feast:
```bash
pip install feast==0.34.1 pyarrow==14.0.1
```

2. Generate feature data:
```bash
python feature_store/generate_features.py
```

3. Initialize feature store:
```bash
python feature_store/setup_feature_store.py
```

### Kubernetes Deployment

1. Apply feature store configuration:
```bash
kubectl apply -f k8s/feature-store.yaml
```

2. Verify deployment:
```bash
kubectl get pods -n mlops-platform -l app=feature-store-registry
kubectl logs -n mlops-platform feature-store-materialization-<pod-id>
```

### AWS Setup (Production)

1. Create S3 bucket for feature storage:
```bash
aws s3 mb s3://mlops-feature-store
```

2. Create DynamoDB table for online store:
```bash
aws dynamodb create-table \
    --table-name feast_online_store \
    --attribute-definitions \
        AttributeName=entity_id,AttributeType=S \
        AttributeName=feature_name,AttributeType=S \
    --key-schema \
        AttributeName=entity_id,KeyType=HASH \
        AttributeName=feature_name,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST
```

3. Update IAM roles with permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": [
        "arn:aws:s3:::mlops-feature-store/*",
        "arn:aws:dynamodb:*:*:table/feast_online_store"
      ]
    }
  ]
}
```

## Troubleshooting

### Feature Not Found

```
feast.errors.FeatureViewNotFoundException: Feature view 'xyz' not found
```

**Solution**: Run `python feature_store/setup_feature_store.py` to register features.

### Materialization Failed

```
feast.errors.MaterializationJobFailure: No data found in source
```

**Solution**: Ensure feature data exists in parquet files and timestamps are recent.

### Online Store Empty

**Check**: Features may not be materialized yet.

```python
from datetime import datetime, timedelta
store.materialize(
    start_date=datetime.now() - timedelta(days=1),
    end_date=datetime.now()
)
```

### High Latency

- Reduce number of features retrieved
- Use feature services instead of individual feature views
- Enable online store caching
- Optimize feature computation

## Migration Guide

### From Manual Features to Feature Store

1. **Identify current features** in your codebase
2. **Define feature views** in `feature_repo.py`
3. **Generate historical data** for offline store
4. **Materialize to online store**
5. **Update training pipeline** to use `get_training_features()`
6. **Update serving** to use `get_features_for_prediction()`
7. **Test end-to-end** with sample data
8. **Deploy incrementally** with feature flags

## Roadmap

### Short-term
- [ ] Add feature monitoring and alerting
- [ ] Implement feature drift detection
- [ ] Add feature lineage tracking
- [ ] Create feature discovery UI

### Medium-term
- [ ] Real-time feature computation with Flink/Spark
- [ ] Feature store UI for non-technical users
- [ ] Automated feature engineering
- [ ] Feature store federation (multi-region)

## Resources

- **Feast Documentation**: https://docs.feast.dev
- **Example Notebooks**: `notebooks/feature_store_demo.ipynb`
- **Feature Registry**: Browse features at `/features/ui` (when UI is enabled)
- **Slack Channel**: #ml-feature-store

## Support

For questions or issues:
1. Check this documentation
2. Review Feast logs: `kubectl logs -n mlops-platform <pod-name>`
3. Contact ML Platform team: ml-platform@company.com
