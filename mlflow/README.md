# MLflow Integration

This directory contains MLflow setup for experiment tracking, model versioning, and model registry.

## Components

### MLflow Server
- **Purpose**: Centralized tracking server for experiments and models
- **Port**: 5000
- **Backend Store**: PostgreSQL database
- **Artifact Store**: Persistent volume (20GB)

### PostgreSQL Database
- **Purpose**: MLflow backend store for metadata
- **Port**: 5432
- **Storage**: 5GB PVC
- **Database**: `mlflow`
- **User/Password**: `mlflow/mlflow` (change in production)

## Features

### Experiment Tracking
- **Parameters**: n_estimators, random_state, n_samples, n_features
- **Metrics**: accuracy, precision, recall
- **Artifacts**: Model files, training data, plots
- **Experiment**: `churn-prediction`

### Model Registry
- **Registered Model**: `churn-prediction-model`
- **Model Signature**: Automatic schema inference
- **Versioning**: Automatic version tracking
- **Stages**: None → Staging → Production → Archived

## Deployment

### Prerequisites
- Kubernetes cluster running
- kubectl configured
- `mlops-platform` namespace exists

### Deploy MLflow Stack

```bash
# Create namespace if needed
kubectl create namespace mlops-platform

# Deploy PostgreSQL backend
kubectl apply -f mlflow/postgres-deployment.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=mlflow-postgres -n mlops-platform --timeout=120s

# Deploy MLflow server
kubectl apply -f mlflow/mlflow-config.yaml
kubectl apply -f mlflow/mlflow-deployment.yaml
kubectl apply -f mlflow/mlflow-service.yaml
```

### Verify Deployment

```bash
# Check pod status
kubectl get pods -n mlops-platform

# Expected output:
# NAME                               READY   STATUS    RESTARTS   AGE
# mlflow-server-xxx                  1/1     Running   0          2m
# mlflow-postgres-xxx                1/1     Running   0          3m

# Check services
kubectl get svc -n mlops-platform | grep mlflow
```

## Access MLflow UI

### Local Development (Port Forwarding)

```bash
# Forward MLflow UI port
kubectl port-forward -n mlops-platform svc/mlflow-server 5000:5000

# Open browser
open http://localhost:5000
```

### Production (via Ingress)

Add to `k8s/ingress.yaml`:

```yaml
- path: /mlflow
  pathType: Prefix
  backend:
    service:
      name: mlflow-server
      port:
        number: 5000
```

## Training with MLflow

### Local Training

```bash
# Set MLflow tracking URI
export MLFLOW_TRACKING_URI=http://localhost:5000

# Port forward if using Kubernetes
kubectl port-forward -n mlops-platform svc/mlflow-server 5000:5000 &

# Train model
cd src
python train.py
```

### Training Output

```
Generating training data...
Preparing features...
Training model...

Model Performance:
  Accuracy:  0.847
  Precision: 0.821
  Recall:    0.765

Model saved to models/churn_model.pkl

MLflow run ID: abc123def456
```

### View Results

1. **Open MLflow UI**: http://localhost:5000
2. **Navigate to**: Experiments → churn-prediction
3. **View run**: Click on the latest run
4. **Inspect**:
   - Parameters: n_estimators, random_state, etc.
   - Metrics: accuracy, precision, recall
   - Artifacts: Model files
   - Models: Registered model versions

## Model Registry

### List Model Versions

```python
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("http://localhost:5000")
client = MlflowClient()

# Get all versions
versions = client.search_model_versions("name='churn-prediction-model'")
for v in versions:
    print(f"Version {v.version}: Stage={v.current_stage}, Run ID={v.run_id}")
```

### Promote Model to Production

```bash
# Via Python
from mlflow.tracking import MlflowClient
client = MlflowClient()
client.transition_model_version_stage(
    name="churn-prediction-model",
    version=1,
    stage="Production"
)

# Or via CLI
mlflow models serve -m "models:/churn-prediction-model/Production" -p 8001
```

### Load Model from Registry

```python
import mlflow.pyfunc

# Load latest production model
model_uri = "models:/churn-prediction-model/Production"
model = mlflow.pyfunc.load_model(model_uri)

# Make predictions
predictions = model.predict(X_test)
```

## Integration with Training Pipeline

The `src/train.py` script now includes:

1. **MLflow Setup**:
   ```python
   mlflow.set_tracking_uri("http://localhost:5000")
   mlflow.set_experiment("churn-prediction")
   ```

2. **Run Context**:
   ```python
   with mlflow.start_run(run_name="churn-model-training"):
       # Training code
   ```

3. **Parameter Logging**:
   ```python
   mlflow.log_param("n_estimators", 100)
   mlflow.log_param("random_state", 42)
   ```

4. **Metric Logging**:
   ```python
   mlflow.log_metric("accuracy", metrics["accuracy"])
   mlflow.log_metric("precision", metrics["precision"])
   ```

5. **Model Logging**:
   ```python
   mlflow.sklearn.log_model(
       model.model,
       "model",
       registered_model_name="churn-prediction-model"
   )
   ```

## CI/CD Integration

Update `.github/workflows/test.yml` to use MLflow:

```yaml
- name: Start MLflow server (test mode)
  run: |
    mlflow server \
      --backend-store-uri sqlite:///mlflow.db \
      --default-artifact-root ./mlruns \
      --host 127.0.0.1 \
      --port 5000 &
    sleep 5

- name: Train model with MLflow
  run: |
    export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
    cd src && python train.py
```

## Experiment Comparison

### Compare Multiple Runs

```python
import mlflow
from mlflow.tracking import MlflowClient

client = MlflowClient()
experiment = client.get_experiment_by_name("churn-prediction")
runs = client.search_runs(experiment.experiment_id)

for run in runs:
    print(f"Run ID: {run.info.run_id}")
    print(f"  Accuracy: {run.data.metrics['accuracy']:.3f}")
    print(f"  Precision: {run.data.metrics['precision']:.3f}")
    print(f"  n_estimators: {run.data.params['n_estimators']}")
    print()
```

### Visualize in UI

1. Go to MLflow UI
2. Select multiple runs (checkbox)
3. Click "Compare" button
4. View parallel coordinates plot
5. Analyze metric distributions

## Best Practices

### 1. Experiment Organization
```python
# Use descriptive experiment names
mlflow.set_experiment("churn-prediction-v2-feature-engineering")

# Use meaningful run names
with mlflow.start_run(run_name=f"rf-{n_estimators}-{datetime.now()}"):
    pass
```

### 2. Comprehensive Logging
```python
# Log hyperparameters
mlflow.log_params(params_dict)

# Log metrics over time
for epoch in range(epochs):
    mlflow.log_metric("loss", loss, step=epoch)

# Log artifacts
mlflow.log_artifact("confusion_matrix.png")
mlflow.log_dict(feature_importance, "feature_importance.json")
```

### 3. Model Metadata
```python
# Add tags
mlflow.set_tag("team", "ml-ops")
mlflow.set_tag("model_type", "random_forest")

# Add description
client.update_registered_model(
    name="churn-prediction-model",
    description="Customer churn prediction using Random Forest"
)
```

### 4. Model Validation
```python
# Load and validate before promotion
model = mlflow.pyfunc.load_model(f"runs:/{run_id}/model")
test_accuracy = evaluate(model, X_test, y_test)

if test_accuracy > 0.85:
    client.transition_model_version_stage(
        name="churn-prediction-model",
        version=version,
        stage="Production"
    )
```

## Troubleshooting

### MLflow Server Not Starting

```bash
# Check logs
kubectl logs -n mlops-platform deployment/mlflow-server

# Check PostgreSQL connection
kubectl exec -n mlops-platform deployment/mlflow-postgres -- \
  psql -U mlflow -d mlflow -c "SELECT 1"
```

### Cannot Connect from Training Script

```bash
# Test connectivity
kubectl port-forward -n mlops-platform svc/mlflow-server 5000:5000
curl http://localhost:5000/health

# Check environment variable
echo $MLFLOW_TRACKING_URI
```

### Artifacts Not Saving

```bash
# Check PVC
kubectl get pvc -n mlops-platform mlflow-artifacts-storage

# Check permissions
kubectl exec -n mlops-platform deployment/mlflow-server -- ls -la /mlflow/artifacts
```

### Database Connection Errors

```bash
# Verify PostgreSQL credentials
kubectl get secret -n mlops-platform postgres-credentials -o yaml

# Test connection
kubectl run -it --rm psql-test --image=postgres:15-alpine -n mlops-platform -- \
  psql -h postgres -U mlflow -d mlflow
```

## Resource Requirements

| Component | CPU Request | Memory Request | CPU Limit | Memory Limit | Storage |
|-----------|-------------|----------------|-----------|--------------|---------|
| MLflow Server | 500m | 512Mi | 1000m | 1Gi | 20Gi (artifacts) |
| PostgreSQL | 250m | 256Mi | 500m | 512Mi | 5Gi (database) |

## Scaling Considerations

For production environments:

1. **High Availability**:
   - Use managed PostgreSQL (AWS RDS, GCP Cloud SQL)
   - Deploy multiple MLflow server replicas
   - Use object storage for artifacts (S3, GCS)

2. **Security**:
   - Enable authentication (basic auth, OAuth)
   - Use Kubernetes secrets for credentials
   - Encrypt backend store connection
   - Network policies to restrict access

3. **Performance**:
   - Index database tables
   - Use connection pooling
   - Enable artifact caching
   - Configure artifact store cleanup

## Next Steps

1. Add model comparison dashboards
2. Integrate with CI/CD for automatic retraining
3. Set up model performance monitoring
4. Create automated model promotion pipeline
5. Add A/B testing framework
6. Implement model rollback procedures
