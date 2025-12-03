# Monitoring Stack

This directory contains Prometheus and Grafana configurations for monitoring the Churn Prediction API.

## Components

### Prometheus
- **Purpose**: Metrics collection and alerting
- **Port**: 9090
- **Retention**: 30 days
- **Storage**: 10GB PVC

### Grafana
- **Purpose**: Metrics visualization and dashboards
- **Port**: 3000
- **Default credentials**: admin/admin
- **Storage**: 5GB PVC

## Metrics Collected

### Application Metrics
- `churn_predictions_total` - Total predictions by result (churn/no_churn)
- `churn_prediction_duration_seconds` - Prediction latency histogram
- `churn_model_confidence` - Current model confidence score
- `churn_predictions_in_progress` - Active prediction requests

### HTTP Metrics (from prometheus-fastapi-instrumentator)
- `http_requests_total` - Total HTTP requests by method, handler, status
- `http_request_duration_seconds` - Request duration histogram
- `http_request_size_bytes` - Request size histogram
- `http_response_size_bytes` - Response size histogram

## Dashboards

### 1. API Overview
- Request rate and latency
- Total predictions and prediction rate
- Churn rate gauge
- Model confidence trends
- Error rates
- Prediction latency distribution

### 2. Model Performance
- Prediction distribution (pie chart)
- Hourly churn rate trend
- Average model confidence
- Predictions per hour
- Latency percentiles (p50, p95, p99)
- Daily prediction volume
- Prediction success rate

## Alerts

Configured alerts in `prometheus-alerts.yaml`:

| Alert | Threshold | Duration | Severity |
|-------|-----------|----------|----------|
| HighErrorRate | > 5% | 5m | Critical |
| SlowAPIResponse | p95 > 2s | 5m | Warning |
| LowPredictionThroughput | < 0.01/s | 10m | Warning |
| ModelNotLoaded | - | 2m | Critical |
| HighChurnRate | > 50% | 30m | Info |
| APIPodDown | - | 2m | Critical |

## Deployment

### Prerequisites
- Kubernetes cluster running
- kubectl configured
- `mlops-platform` namespace exists

### Deploy Monitoring Stack

```bash
# Create namespace if needed
kubectl create namespace mlops-platform

# Deploy Prometheus
kubectl apply -f monitoring/prometheus-config.yaml
kubectl apply -f monitoring/prometheus-alerts.yaml
kubectl apply -f monitoring/prometheus-deployment.yaml
kubectl apply -f monitoring/prometheus-service.yaml

# Deploy Grafana
kubectl apply -f monitoring/grafana-datasource.yaml
kubectl apply -f monitoring/grafana-dashboards-config.yaml
kubectl apply -f monitoring/grafana-dashboards.yaml
kubectl apply -f monitoring/grafana-deployment.yaml
kubectl apply -f monitoring/grafana-service.yaml
```

### Verify Deployment

```bash
# Check pod status
kubectl get pods -n mlops-platform

# Expected output:
# NAME                                     READY   STATUS    RESTARTS   AGE
# prometheus-xxx                           1/1     Running   0          2m
# grafana-xxx                              1/1     Running   0          2m
# churn-prediction-api-xxx                 1/1     Running   0          5m
```

## Access Services

### Local Development (Port Forwarding)

```bash
# Access Prometheus
kubectl port-forward -n mlops-platform svc/prometheus 9090:9090
# Open: http://localhost:9090

# Access Grafana
kubectl port-forward -n mlops-platform svc/grafana 3000:3000
# Open: http://localhost:3000
# Login: admin/admin
```

### Production (via Ingress)

Update `k8s/ingress.yaml` to include:

```yaml
- path: /prometheus
  pathType: Prefix
  backend:
    service:
      name: prometheus
      port:
        number: 9090
- path: /grafana
  pathType: Prefix
  backend:
    service:
      name: grafana
      port:
        number: 3000
```

## Testing Metrics

### View Metrics Endpoint

```bash
# Port forward API
kubectl port-forward -n mlops-platform svc/churn-prediction-api 8000:8000

# Access metrics
curl http://localhost:8000/metrics
```

### Generate Test Traffic

```bash
# Make prediction requests
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/v1/predict \
    -H "Content-Type: application/json" \
    -d '{
      "tenure_months": 12,
      "monthly_charges": 70.5,
      "total_charges": 850,
      "contract_type": "Month-to-month",
      "num_support_tickets": 3
    }'
  sleep 0.1
done
```

## Querying Metrics in Prometheus

Example PromQL queries:

```promql
# Total predictions in last hour
increase(churn_predictions_total[1h])

# Churn rate
rate(churn_predictions_total{prediction_result="churn"}[5m]) / 
rate(churn_predictions_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(churn_prediction_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / 
rate(http_requests_total[5m])
```

## Grafana Setup

1. **Access Grafana** at http://localhost:3000
2. **Login** with admin/admin
3. **Dashboards** are auto-provisioned:
   - Navigate to Dashboards → MLOps Platform folder
   - Select "Churn Prediction API - Overview" or "Churn Model Performance"

## Troubleshooting

### Prometheus not scraping metrics

```bash
# Check Prometheus targets
kubectl port-forward -n mlops-platform svc/prometheus 9090:9090
# Open: http://localhost:9090/targets

# Verify API pods have correct labels
kubectl get pods -n mlops-platform -l app=churn-prediction-api --show-labels
```

### Grafana dashboards not loading

```bash
# Check Grafana logs
kubectl logs -n mlops-platform deployment/grafana

# Verify datasource
kubectl get cm -n mlops-platform grafana-datasource -o yaml
```

### No metrics appearing

```bash
# Test metrics endpoint directly
kubectl exec -n mlops-platform deployment/churn-prediction-api -- curl localhost:8000/metrics

# Check if prometheus-fastapi-instrumentator is installed
kubectl exec -n mlops-platform deployment/churn-prediction-api -- pip list | grep prometheus
```

## Scaling Considerations

For production environments:

1. **Prometheus**:
   - Increase storage to 50GB+
   - Consider Thanos for long-term storage
   - Set up remote write to centralized storage

2. **Grafana**:
   - Use external database (PostgreSQL) instead of SQLite
   - Enable authentication (OAuth, LDAP)
   - Configure user roles and permissions

3. **Alerts**:
   - Configure Alertmanager for notifications (Slack, PagerDuty, email)
   - Set up on-call rotations
   - Create runbooks for each alert

## Resource Requirements

| Component | CPU Request | Memory Request | CPU Limit | Memory Limit | Storage |
|-----------|-------------|----------------|-----------|--------------|---------|
| Prometheus | 500m | 512Mi | 1000m | 1Gi | 10Gi |
| Grafana | 250m | 256Mi | 500m | 512Mi | 5Gi |

## Next Steps

1. Configure Alertmanager for notifications
2. Add business metrics (revenue impact, customer segments)
3. Set up log aggregation (ELK/Loki)
4. Create SLIs/SLOs for API reliability
5. Implement distributed tracing (Jaeger/Tempo)
