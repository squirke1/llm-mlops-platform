# A/B Testing Configuration

This directory contains configuration files for A/B testing model versions.

## Overview

The A/B testing system allows you to:
- Test new model versions against production models
- Route traffic based on different strategies (random, hash-based, sticky)
- Track performance metrics for each model variant
- Gradually roll out new models with controlled traffic splits

## Configuration Methods

### 1. Environment Variables

Set these environment variables to configure A/B testing:

```bash
# Enable A/B testing
export AB_TESTING_ENABLED=true

# Set routing strategy: random, hash, or sticky
export AB_ROUTING_STRATEGY=random

# Configure traffic split (variant_name:percentage,variant_name:percentage)
export AB_TRAFFIC_CONFIG="production:90,staging:10"
```

### 2. Kubernetes ConfigMap

Create a ConfigMap for A/B testing configuration:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ab-testing-config
  namespace: mlops-platform
data:
  AB_TESTING_ENABLED: "true"
  AB_ROUTING_STRATEGY: "hash"
  AB_TRAFFIC_CONFIG: "production:90,staging:10"
```

Apply the ConfigMap:

```bash
kubectl apply -f ab-testing-config.yaml
```

Update your deployment to use the ConfigMap:

```yaml
envFrom:
  - configMapRef:
      name: ab-testing-config
```

## Routing Strategies

### Random Routing
- Distributes traffic randomly based on configured percentages
- Good for: Quick experiments, simple A/B tests
- Usage: `AB_ROUTING_STRATEGY=random`

### Hash-Based Routing
- Consistent routing based on user_id hash
- Same user always gets same variant
- Good for: User experience consistency, longer experiments
- Usage: `AB_ROUTING_STRATEGY=hash`
- Requires: `user_id` parameter in prediction requests

### Sticky Routing
- Consistent routing based on session_id hash
- Same session always gets same variant
- Good for: Session-based experiments
- Usage: `AB_ROUTING_STRATEGY=sticky`
- Requires: `session_id` parameter in prediction requests

## Traffic Split Examples

### Canary Deployment (5% new model)
```bash
export AB_TRAFFIC_CONFIG="production:95,staging:5"
```

### 50/50 Split Test
```bash
export AB_TRAFFIC_CONFIG="production:50,staging:50"
```

### Multi-variant Test
```bash
export AB_TRAFFIC_CONFIG="production:70,variant_a:15,variant_b:15"
```

## Model Stages

The system automatically assigns stages to variants:

- **champion**: Current production model (control group)
- **challenger**: New model being tested (treatment group)
- **control**: Baseline model for comparison
- **treatment**: Experimental model variant

## Monitoring A/B Tests

### Check A/B Test Status

```bash
curl http://api-endpoint/api/v1/ab-test/status
```

Response:
```json
{
  "active_variants": 2,
  "routing_strategy": "hash",
  "variants": [
    {
      "name": "production",
      "version": "production",
      "stage": "champion",
      "traffic_percentage": 90
    },
    {
      "name": "staging",
      "version": "staging",
      "stage": "challenger",
      "traffic_percentage": 10
    }
  ]
}
```

### Prometheus Metrics

The A/B testing system exposes these metrics:

```promql
# Total requests per variant
ab_test_requests_total{variant_name="production", variant_version="production"}

# Prediction duration per variant
ab_test_prediction_duration_seconds{variant_name="production", variant_version="production"}

# Errors per variant
ab_test_errors_total{variant_name="production", variant_version="production"}
```

### Compare Variant Performance

```promql
# Request rate per variant
rate(ab_test_requests_total[5m])

# Average latency per variant
rate(ab_test_prediction_duration_seconds_sum[5m]) / 
rate(ab_test_prediction_duration_seconds_count[5m])

# Error rate per variant
rate(ab_test_errors_total[5m]) / 
rate(ab_test_requests_total[5m])
```

## Making Predictions with A/B Testing

### Basic Request (Random Routing)

```bash
curl -X POST http://api-endpoint/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "tenure_months": 24,
    "monthly_charges": 79.99,
    "total_charges": 1919.76,
    "contract_type": "Month-to-month",
    "num_support_tickets": 3
  }'
```

### With User ID (Hash-Based Routing)

```bash
curl -X POST "http://api-endpoint/api/v1/predict?user_id=user123" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### With Session ID (Sticky Routing)

```bash
curl -X POST "http://api-endpoint/api/v1/predict?session_id=sess456" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

Response includes variant information:

```json
{
  "prediction": 1,
  "probability": 0.73,
  "model_variant": "staging",
  "model_version": "staging"
}
```

## Gradual Rollout Strategy

### Phase 1: Initial Test (5%)
```bash
export AB_TRAFFIC_CONFIG="production:95,staging:5"
```
- Monitor for 1-3 days
- Check error rates, latency, accuracy

### Phase 2: Expand (20%)
```bash
export AB_TRAFFIC_CONFIG="production:80,staging:20"
```
- Monitor for 3-7 days
- Validate business metrics

### Phase 3: Majority Traffic (50%)
```bash
export AB_TRAFFIC_CONFIG="production:50,staging:50"
```
- Monitor for 7-14 days
- Statistical significance

### Phase 4: Full Rollout (100%)
```bash
# Promote staging to production in MLflow
# Disable A/B testing
export AB_TESTING_ENABLED=false
```

## Best Practices

### 1. Statistical Significance
- Run tests long enough for statistical significance
- Minimum sample size: 1000+ predictions per variant
- Recommended duration: 7-14 days

### 2. Metrics to Track
- **Performance**: Latency, error rate
- **Accuracy**: Precision, recall, F1 score
- **Business**: Conversion rate, revenue impact
- **User Experience**: User satisfaction, engagement

### 3. Safety Guidelines
- Start with small traffic percentages (5-10%)
- Monitor closely during first 24 hours
- Set up alerts for anomalies
- Have rollback plan ready

### 4. Rollback Procedure
```bash
# Quick rollback to production only
export AB_TRAFFIC_CONFIG="production:100,staging:0"

# Or disable A/B testing
export AB_TESTING_ENABLED=false

# Restart API pods
kubectl rollout restart deployment/churn-api -n mlops-platform
```

## Grafana Dashboard

Add these panels to your Grafana dashboard:

### Variant Traffic Distribution
```promql
sum by (variant_name) (rate(ab_test_requests_total[5m]))
```

### Variant Latency Comparison
```promql
histogram_quantile(0.95,
  rate(ab_test_prediction_duration_seconds_bucket[5m])
) by (variant_name)
```

### Variant Error Rates
```promql
sum by (variant_name) (rate(ab_test_errors_total[5m])) /
sum by (variant_name) (rate(ab_test_requests_total[5m]))
```

## Troubleshooting

### A/B Testing Not Working

Check configuration:
```bash
# View API logs
kubectl logs -l app=churn-api -n mlops-platform | grep "A/B"

# Check environment variables
kubectl exec deployment/churn-api -n mlops-platform -- env | grep AB_
```

### Uneven Traffic Distribution

- Verify traffic percentages sum to 100
- Check routing strategy is appropriate
- For hash-based: Ensure user_id is provided
- For sticky: Ensure session_id is provided

### Metrics Not Updating

```bash
# Check Prometheus targets
curl http://prometheus:9090/api/v1/targets

# Query metrics directly
curl http://api:8000/metrics | grep ab_test
```

## References

- [MLflow Model Registry](../mlflow/README.md)
- [Monitoring Guide](../monitoring/README.md)
- [API Documentation](http://api-endpoint/docs)
