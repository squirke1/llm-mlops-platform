# Runbooks

Operational runbooks for incident response and troubleshooting the MLOps platform.

## Quick Reference

| Alert | Severity | Runbook |
|-------|----------|---------|
| HighErrorRate | Critical | [High Error Rate](#high-error-rate) |
| SlowAPIResponse | Warning | [Slow API Response](#slow-api-response) |
| APIPodDown | Critical | [API Pod Down](#api-pod-down) |
| MLflowServerDown | Critical | [MLflow Server Down](#mlflow-server-down) |
| PostgreSQLDown | Critical | [PostgreSQL Down](#postgresql-down) |
| BackupJobFailed | Critical | [Backup Job Failed](#backup-job-failed) |
| HighCPUUsage | Warning | [High CPU Usage](#high-cpu-usage) |
| HighMemoryUsage | Warning | [High Memory Usage](#high-memory-usage) |
| PodRestartLoop | Warning | [Pod Restart Loop](#pod-restart-loop) |

---

## Application Alerts

### High Error Rate

**Alert**: `HighErrorRate`  
**Severity**: Critical  
**Threshold**: > 5% of requests returning 5xx errors for 5 minutes

#### Symptoms
- Increased 5xx HTTP status codes
- Users reporting service errors
- Prediction failures

#### Investigation Steps

1. **Check API logs**
```bash
kubectl logs -l app=churn-api -n mlops-platform --tail=100
```

2. **Check for recent deployments**
```bash
kubectl rollout history deployment/churn-api -n mlops-platform
```

3. **Check model loading**
```bash
# Verify model file exists
kubectl exec -it deployment/churn-api -n mlops-platform -- ls -lh /app/models/

# Check model loading in logs
kubectl logs -l app=churn-api -n mlops-platform | grep -i "model"
```

4. **Check dependencies**
```bash
# MLflow connection
kubectl exec -it deployment/churn-api -n mlops-platform -- \
  curl -f http://mlflow-server:5000/health

# Database connection
kubectl exec -it deployment/churn-api -n mlops-platform -- \
  nc -zv postgres 5432
```

#### Resolution

**If model is missing:**
```bash
# Retrain model
kubectl exec -it deployment/churn-api -n mlops-platform -- python src/train.py

# Or restore from backup
kubectl cp ./models/churn_model.pkl mlops-platform/<pod-name>:/app/models/
```

**If recent deployment caused issue:**
```bash
# Rollback to previous version
kubectl rollout undo deployment/churn-api -n mlops-platform

# Verify rollback
kubectl rollout status deployment/churn-api -n mlops-platform
```

**If dependency issue:**
```bash
# Restart dependent services
kubectl rollout restart deployment/mlflow-server -n mlops-platform
kubectl rollout restart deployment/postgres -n mlops-platform
```

#### Prevention
- Implement canary deployments
- Add pre-deployment model validation
- Set up dependency health checks

---

### Slow API Response

**Alert**: `SlowAPIResponse`  
**Severity**: Warning  
**Threshold**: 95th percentile > 2 seconds for 5 minutes

#### Symptoms
- Increased latency
- Request timeouts
- Poor user experience

#### Investigation Steps

1. **Check response time distribution**
```bash
# Query Prometheus
curl -G http://prometheus:9090/api/v1/query \
  --data-urlencode 'query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))'
```

2. **Check resource usage**
```bash
kubectl top pods -n mlops-platform
kubectl top nodes
```

3. **Check for slow predictions**
```bash
# Look for long-running predictions in logs
kubectl logs -l app=churn-api -n mlops-platform | grep "duration"
```

4. **Check model size**
```bash
kubectl exec -it deployment/churn-api -n mlops-platform -- \
  ls -lh /app/models/churn_model.pkl
```

#### Resolution

**If CPU constrained:**
```bash
# Scale up replicas
kubectl scale deployment/churn-api --replicas=3 -n mlops-platform

# Or increase CPU limits
kubectl patch deployment churn-api -n mlops-platform --patch '
spec:
  template:
    spec:
      containers:
      - name: api
        resources:
          limits:
            cpu: "2"
          requests:
            cpu: "1"
'
```

**If memory constrained:**
```bash
# Increase memory limits
kubectl patch deployment churn-api -n mlops-platform --patch '
spec:
  template:
    spec:
      containers:
      - name: api
        resources:
          limits:
            memory: "2Gi"
          requests:
            memory: "1Gi"
'
```

**If model is slow:**
- Consider model optimization (quantization, pruning)
- Cache predictions for common inputs
- Implement request batching

#### Prevention
- Set up horizontal pod autoscaling
- Implement caching layer
- Optimize model inference

---

### API Pod Down

**Alert**: `APIPodDown`  
**Severity**: Critical  
**Threshold**: Pod unreachable for 2 minutes

#### Symptoms
- Service unavailable
- Health check failures
- No metrics being scraped

#### Investigation Steps

1. **Check pod status**
```bash
kubectl get pods -l app=churn-api -n mlops-platform
kubectl describe pod -l app=churn-api -n mlops-platform
```

2. **Check pod logs**
```bash
kubectl logs -l app=churn-api -n mlops-platform --previous
```

3. **Check events**
```bash
kubectl get events -n mlops-platform --sort-by='.lastTimestamp' | grep churn-api
```

4. **Check node status**
```bash
kubectl get nodes
kubectl describe node <node-name>
```

#### Resolution

**If pod is CrashLoopBackOff:**
```bash
# Check logs for error
kubectl logs -l app=churn-api -n mlops-platform --previous

# Common fixes:
# - Fix configuration
# - Restore missing model file
# - Fix environment variables
```

**If pod is Pending:**
```bash
# Check resource availability
kubectl describe pod -l app=churn-api -n mlops-platform

# Scale down other services if needed
kubectl scale deployment <other-service> --replicas=0 -n mlops-platform
```

**If node is NotReady:**
```bash
# Cordon node
kubectl cordon <node-name>

# Force reschedule pods
kubectl delete pod -l app=churn-api -n mlops-platform

# Check node issues
kubectl describe node <node-name>
```

#### Prevention
- Configure pod anti-affinity
- Set appropriate resource requests/limits
- Use PodDisruptionBudgets
- Monitor node health

---

## Infrastructure Alerts

### MLflow Server Down

**Alert**: `MLflowServerDown`  
**Severity**: Critical  
**Threshold**: Unreachable for 5 minutes

#### Symptoms
- Cannot track experiments
- Model registry unavailable
- API can't load models from registry

#### Investigation Steps

1. **Check MLflow pod status**
```bash
kubectl get pods -l app=mlflow-server -n mlops-platform
kubectl describe pod -l app=mlflow-server -n mlops-platform
```

2. **Check logs**
```bash
kubectl logs -l app=mlflow-server -n mlops-platform --tail=100
```

3. **Check PostgreSQL connection**
```bash
kubectl exec -it deployment/mlflow-server -n mlops-platform -- \
  nc -zv postgres 5432
```

4. **Check storage**
```bash
kubectl exec -it deployment/mlflow-server -n mlops-platform -- df -h
```

#### Resolution

**If database connection failed:**
```bash
# Check PostgreSQL is running
kubectl get pods -l app=mlflow-postgres -n mlops-platform

# Restart MLflow server
kubectl rollout restart deployment/mlflow-server -n mlops-platform
```

**If storage is full:**
```bash
# Expand PVC
kubectl patch pvc mlflow-artifacts-pvc -n mlops-platform --patch '
spec:
  resources:
    requests:
      storage: 30Gi
'

# Clean up old artifacts manually if needed
kubectl exec -it deployment/mlflow-server -n mlops-platform -- \
  find /mlflow/artifacts -type f -mtime +90 -delete
```

**If pod won't start:**
```bash
# Check init container logs
kubectl logs -l app=mlflow-server -n mlops-platform -c wait-for-postgres

# Manually test database
kubectl run -it --rm psql --image=postgres:15-alpine -- \
  psql postgresql://mlflow:mlflow@postgres:5432/mlflow -c "SELECT 1"
```

#### Prevention
- Monitor database connection pool
- Set up automated artifact cleanup
- Configure storage alerts
- Use persistent volumes with auto-expansion

---

### PostgreSQL Down

**Alert**: `PostgreSQLDown`  
**Severity**: Critical  
**Threshold**: Unreachable for 2 minutes

#### Symptoms
- MLflow server errors
- Database connection failures
- Experiment tracking unavailable

#### Investigation Steps

1. **Check PostgreSQL pod**
```bash
kubectl get pods -l app=mlflow-postgres -n mlops-platform
kubectl describe pod -l app=mlflow-postgres -n mlops-platform
```

2. **Check logs**
```bash
kubectl logs -l app=mlflow-postgres -n mlops-platform --tail=100
```

3. **Check PVC**
```bash
kubectl get pvc -n mlops-platform
kubectl describe pvc postgres-pvc -n mlops-platform
```

#### Resolution

**If pod crashed:**
```bash
# Check crash reason in logs
kubectl logs -l app=mlflow-postgres -n mlops-platform --previous

# Common issues:
# - Corrupted data files: Restore from backup
# - Out of disk space: Expand PVC
# - Configuration error: Fix configmap
```

**If data corruption:**
```bash
# Scale down MLflow first
kubectl scale deployment mlflow-server --replicas=0 -n mlops-platform

# Restore database from backup
kubectl create job --from=cronjob/postgres-backup postgres-restore -n mlops-platform

# Scale up MLflow
kubectl scale deployment mlflow-server --replicas=1 -n mlops-platform
```

**If PVC issue:**
```bash
# Check PV status
kubectl get pv

# If PV is Released, you may need to:
# 1. Create new PVC
# 2. Restore data from backup
# 3. Update deployment to use new PVC
```

#### Prevention
- Regular backups (automated with CronJob)
- Monitor disk usage
- Use volume snapshots
- Test restore procedures

---

### Backup Job Failed

**Alert**: `BackupJobFailed`  
**Severity**: Critical  
**Threshold**: Backup job failed

#### Symptoms
- Backup job shows Failed status
- No recent backups in S3
- Backup logs show errors

#### Investigation Steps

1. **Check job status**
```bash
kubectl get jobs -n mlops-platform | grep backup
kubectl describe job <backup-job> -n mlops-platform
```

2. **Check logs**
```bash
kubectl logs job/<backup-job> -n mlops-platform
```

3. **Check storage**
```bash
# Backup PVC
kubectl exec -it <backup-pod> -n mlops-platform -- df -h /backups

# S3 bucket
aws s3 ls s3://mlops-platform-backups/backups/
```

4. **Check IAM permissions**
```bash
kubectl describe sa backup-sa -n mlops-platform
```

#### Resolution

**If disk space issue:**
```bash
# Clean up old backups
kubectl exec -it <backup-pod> -n mlops-platform -- \
  find /backups -name "*.sql.gz" -mtime +7 -delete

# Expand PVC
kubectl patch pvc backup-pvc -n mlops-platform --patch '
spec:
  resources:
    requests:
      storage: 100Gi
'
```

**If S3 access issue:**
```bash
# Verify IAM role
aws sts assume-role --role-arn <role-arn> --role-session-name test

# Test S3 access
kubectl run aws-test --image=amazon/aws-cli -it --rm -- \
  s3 ls s3://mlops-platform-backups/

# Update IAM policy if needed
```

**If database connection issue:**
```bash
# Test database connection
kubectl exec -it <backup-pod> -n mlops-platform -- \
  pg_isready -h postgres -p 5432 -U mlflow

# Check secrets
kubectl get secret postgres-secrets -n mlops-platform -o yaml
```

**Run manual backup:**
```bash
kubectl create job --from=cronjob/postgres-backup postgres-backup-manual -n mlops-platform
kubectl wait --for=condition=complete job/postgres-backup-manual -n mlops-platform --timeout=600s
```

#### Prevention
- Monitor backup job completion
- Set up backup verification
- Test restore procedures monthly
- Configure backup retention policies

---

## Resource Alerts

### High CPU Usage

**Alert**: `HighCPUUsage`  
**Severity**: Warning  
**Threshold**: > 80% CPU for 10 minutes

#### Investigation

```bash
# Check which container
kubectl top pods -n mlops-platform --containers

# Check resource limits
kubectl describe pod <pod-name> -n mlops-platform | grep -A 5 "Limits"
```

#### Resolution

```bash
# Scale horizontally
kubectl scale deployment <deployment-name> --replicas=3 -n mlops-platform

# Or increase CPU limits
kubectl patch deployment <deployment-name> -n mlops-platform --patch '
spec:
  template:
    spec:
      containers:
      - name: <container-name>
        resources:
          limits:
            cpu: "2"
          requests:
            cpu: "1"
'
```

---

### High Memory Usage

**Alert**: `HighMemoryUsage`  
**Severity**: Warning  
**Threshold**: > 85% memory for 10 minutes

#### Investigation

```bash
kubectl top pods -n mlops-platform --containers
kubectl describe pod <pod-name> -n mlops-platform
```

#### Resolution

```bash
# Increase memory limits
kubectl patch deployment <deployment-name> -n mlops-platform --patch '
spec:
  template:
    spec:
      containers:
      - name: <container-name>
        resources:
          limits:
            memory: "2Gi"
          requests:
            memory: "1Gi"
'

# Or restart to clear memory leaks
kubectl rollout restart deployment/<deployment-name> -n mlops-platform
```

---

### Pod Restart Loop

**Alert**: `PodRestartLoop`  
**Severity**: Warning  
**Threshold**: Pod restarting frequently

#### Investigation

```bash
# Check restart count
kubectl get pods -n mlops-platform

# Check logs from previous instance
kubectl logs <pod-name> -n mlops-platform --previous

# Check events
kubectl describe pod <pod-name> -n mlops-platform
```

#### Resolution

Based on crash reason:
- **OOMKilled**: Increase memory limits
- **Error**: Fix application error in logs
- **CrashLoopBackOff**: Check startup dependencies
- **Liveness probe failed**: Adjust probe settings

---

## Escalation

### Severity Levels

- **Critical**: Immediate response required (< 15 minutes)
- **Warning**: Response required within 1 hour
- **Info**: Monitor, no immediate action

### On-Call Contacts

- Primary: [Your team's on-call rotation]
- Secondary: [Backup on-call]
- Infrastructure: [Platform team contact]
- Database: [DBA contact]

### Communication Channels

- Incidents: #mlops-incidents (Slack)
- Updates: #mlops-alerts (Slack)
- Postmortems: Document in wiki

---

## Useful Commands

### Quick Diagnostics

```bash
# Check all pods
kubectl get pods -n mlops-platform -o wide

# Check all services
kubectl get svc -n mlops-platform

# Check resource usage
kubectl top pods -n mlops-platform
kubectl top nodes

# Check PVCs
kubectl get pvc -n mlops-platform

# Recent events
kubectl get events -n mlops-platform --sort-by='.lastTimestamp' | tail -20

# Pod logs
kubectl logs -l app=<app-name> -n mlops-platform --tail=100 -f

# Exec into pod
kubectl exec -it deployment/<deployment-name> -n mlops-platform -- /bin/bash
```

### Prometheus Queries

```promql
# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Response time (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Prediction rate
rate(churn_predictions_total[5m])

# Resource usage
rate(container_cpu_usage_seconds_total{namespace="mlops-platform"}[5m])
```

### Port Forwarding

```bash
# Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n mlops-platform

# Grafana
kubectl port-forward svc/grafana 3000:3000 -n mlops-platform

# MLflow
kubectl port-forward svc/mlflow-server 5000:5000 -n mlops-platform

# API
kubectl port-forward svc/churn-api 8000:8000 -n mlops-platform
```

---

## References

- [Kubernetes Troubleshooting Guide](https://kubernetes.io/docs/tasks/debug/)
- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [PostgreSQL Troubleshooting](https://www.postgresql.org/docs/current/server-start.html)
- Internal wiki: [Your wiki link]
