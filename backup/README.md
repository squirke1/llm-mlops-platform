# Backup and Disaster Recovery

Comprehensive backup strategy for the MLOps platform to ensure data protection and business continuity.

## Overview

### What's Backed Up

1. **PostgreSQL Database** (MLflow metadata)
   - Experiment tracking data
   - Model registry metadata
   - User configurations
   - Schedule: Daily at 2 AM

2. **MLflow Artifacts** (model files, plots, etc.)
   - Model binaries
   - Training artifacts
   - Visualizations
   - Schedule: Daily at 3 AM

3. **Kubernetes Configurations**
   - Deployment manifests
   - ConfigMaps and Secrets
   - Schedule: On-demand

### Backup Locations

- **Primary**: Kubernetes PVC (50GB)
- **Secondary**: AWS S3 (optional, recommended for production)
- **Retention**: 7 days local, 90 days S3

## Setup

### 1. Deploy Backup Infrastructure

```bash
# Create backup namespace resources
kubectl apply -f backup/backup-cronjobs.yaml

# Verify CronJobs
kubectl get cronjobs -n mlops-platform
```

### 2. Configure S3 (Production)

#### Create S3 Bucket

```bash
# Create bucket
aws s3 mb s3://mlops-platform-backups

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket mlops-platform-backups \
  --versioning-configuration Status=Enabled

# Set lifecycle policy (retain 90 days)
cat > lifecycle.json <<EOF
{
  "Rules": [{
    "Id": "DeleteOldBackups",
    "Status": "Enabled",
    "Expiration": {
      "Days": 90
    }
  }]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket mlops-platform-backups \
  --lifecycle-configuration file://lifecycle.json
```

#### Create IAM Role for Backup

```bash
# Create IAM policy
cat > backup-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::mlops-platform-backups",
        "arn:aws:s3:::mlops-platform-backups/*"
      ]
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name MLOpsBackupPolicy \
  --policy-document file://backup-policy.json

# Create IAM role for IRSA (EKS)
eksctl create iamserviceaccount \
  --name backup-sa \
  --namespace mlops-platform \
  --cluster <cluster-name> \
  --attach-policy-arn arn:aws:iam::<account>:policy/MLOpsBackupPolicy \
  --approve
```

### 3. Update CronJob Configuration

Edit `backup-cronjobs.yaml` and set your S3 bucket:

```yaml
- name: AWS_S3_BUCKET
  value: "mlops-platform-backups"  # Your bucket name
```

## Manual Backup

### PostgreSQL

```bash
# Run backup job immediately
kubectl create job --from=cronjob/postgres-backup postgres-backup-manual -n mlops-platform

# Check status
kubectl get jobs -n mlops-platform
kubectl logs job/postgres-backup-manual -n mlops-platform

# Download backup locally
kubectl cp mlops-platform/<backup-pod>:/backups/postgres/mlflow_20231201_120000.sql.gz ./backup.sql.gz
```

### MLflow Artifacts

```bash
# Run artifacts backup
kubectl create job --from=cronjob/mlflow-artifacts-backup artifacts-backup-manual -n mlops-platform

# Check status
kubectl logs job/artifacts-backup-manual -n mlops-platform
```

### Manual Database Dump

```bash
# Port-forward to PostgreSQL
kubectl port-forward svc/postgres 5432:5432 -n mlops-platform

# Dump database
PGPASSWORD=<password> pg_dump \
  -h localhost \
  -U mlflow \
  -d mlflow \
  --format=custom \
  --file=mlflow_backup_$(date +%Y%m%d).dump
```

## Restore Procedures

### Restore PostgreSQL

#### Method 1: From Kubernetes Backup

```bash
# Copy backup to restore pod
kubectl cp ./backup.sql.gz mlops-platform/<postgres-pod>:/tmp/restore.sql.gz

# Exec into pod
kubectl exec -it <postgres-pod> -n mlops-platform -- /bin/bash

# Restore
gunzip -c /tmp/restore.sql.gz | psql -U mlflow -d mlflow
```

#### Method 2: From S3

```bash
# Create restore job
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: postgres-restore
  namespace: mlops-platform
spec:
  template:
    spec:
      serviceAccountName: backup-sa
      restartPolicy: Never
      containers:
      - name: restore
        image: postgres:15-alpine
        command:
        - /bin/bash
        - /scripts/restore-postgres.sh
        - s3://mlops-platform-backups/backups/postgres/mlflow_20231201_020000.sql.gz
        env:
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: postgres-user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: postgres-password
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: postgres-db
        volumeMounts:
        - name: backup-scripts
          mountPath: /scripts
      volumes:
      - name: backup-scripts
        configMap:
          name: backup-scripts
          defaultMode: 0755
EOF

# Monitor restore
kubectl logs job/postgres-restore -n mlops-platform -f
```

### Restore MLflow Artifacts

```bash
# Scale down MLflow server
kubectl scale deployment mlflow-server --replicas=0 -n mlops-platform

# Create restore job
cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: artifacts-restore
  namespace: mlops-platform
spec:
  template:
    spec:
      serviceAccountName: backup-sa
      restartPolicy: Never
      containers:
      - name: restore
        image: alpine:3.18
        command:
        - /bin/sh
        - -c
        - |
          # Download from S3
          aws s3 cp s3://mlops-platform-backups/backups/artifacts/artifacts_20231201_030000.tar.gz /tmp/restore.tar.gz
          
          # Extract to artifacts directory
          tar -xzf /tmp/restore.tar.gz -C /mlflow/artifacts
          
          echo "Restore completed"
        volumeMounts:
        - name: mlflow-artifacts
          mountPath: /mlflow/artifacts
      volumes:
      - name: mlflow-artifacts
        persistentVolumeClaim:
          claimName: mlflow-artifacts-pvc
EOF

# Wait for completion
kubectl wait --for=condition=complete job/artifacts-restore -n mlops-platform --timeout=600s

# Scale up MLflow server
kubectl scale deployment mlflow-server --replicas=1 -n mlops-platform
```

## Disaster Recovery Plan

### RTO and RPO Targets

- **Recovery Time Objective (RTO)**: 4 hours
- **Recovery Point Objective (RPO)**: 24 hours

### Full System Recovery

#### Step 1: Restore Infrastructure

```bash
# Recreate Kubernetes cluster
terraform apply -target=module.eks

# Deploy base manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f secrets/secrets.yaml
```

#### Step 2: Restore Persistent Data

```bash
# Deploy PostgreSQL
kubectl apply -f mlflow/postgres-deployment.yaml

# Wait for PostgreSQL
kubectl wait --for=condition=ready pod -l app=mlflow-postgres -n mlops-platform --timeout=300s

# Restore database
kubectl create job --from=cronjob/postgres-backup postgres-restore -n mlops-platform
# (use restore procedure above)
```

#### Step 3: Restore MLflow

```bash
# Deploy MLflow server
kubectl apply -f mlflow/mlflow-deployment.yaml

# Restore artifacts
# (use artifacts restore procedure above)
```

#### Step 4: Restore Application

```bash
# Deploy API
kubectl apply -f k8s/deployment.yaml

# Deploy monitoring
kubectl apply -f monitoring/prometheus-deployment.yaml
kubectl apply -f monitoring/grafana-deployment.yaml
```

#### Step 5: Verify

```bash
# Check all pods
kubectl get pods -n mlops-platform

# Test API
curl http://<api-endpoint>/health

# Test MLflow
curl http://<mlflow-endpoint>/health

# Verify metrics
curl http://<prometheus-endpoint>/api/v1/query?query=up
```

### Testing DR Plan

Run quarterly disaster recovery drills:

```bash
# 1. Create test namespace
kubectl create namespace dr-test

# 2. Deploy with backups
# (follow restore procedures in dr-test namespace)

# 3. Verify functionality
kubectl run test-pod --image=curlimages/curl -n dr-test -- \
  curl http://churn-api.dr-test:8000/health

# 4. Clean up
kubectl delete namespace dr-test
```

## Monitoring Backups

### Check Backup Status

```bash
# View CronJob status
kubectl get cronjobs -n mlops-platform

# View recent jobs
kubectl get jobs -n mlops-platform

# View job logs
kubectl logs -l job-name=postgres-backup -n mlops-platform

# Check S3 backups
aws s3 ls s3://mlops-platform-backups/backups/ --recursive
```

### Backup Alerts

Add to `monitoring/alerting-rules.yaml`:

```yaml
- alert: BackupJobFailed
  expr: kube_job_status_failed{namespace="mlops-platform"} > 0
  for: 1h
  labels:
    severity: critical
  annotations:
    summary: "Backup job failed"
    description: "Backup job {{ $labels.job_name }} has failed"

- alert: BackupJobMissing
  expr: |
    (time() - kube_job_status_completion_time{namespace="mlops-platform",job_name=~".*backup.*"}) > 86400 * 2
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "Backup job hasn't run"
    description: "Backup job {{ $labels.job_name }} hasn't completed in 48 hours"
```

## Best Practices

1. **Test Restores Regularly**
   - Monthly restore drills
   - Verify data integrity
   - Document restore time

2. **Multiple Backup Locations**
   - Local PVC for fast recovery
   - S3 for disaster recovery
   - Cross-region replication for S3

3. **Encrypt Backups**
   - Enable S3 encryption at rest
   - Use KMS for key management
   - Encrypt backups before upload

4. **Monitor Backup Health**
   - Alert on failed backups
   - Track backup size trends
   - Verify backup completeness

5. **Document Procedures**
   - Keep runbooks updated
   - Document dependencies
   - List required credentials

6. **Automate Where Possible**
   - Use CronJobs for regular backups
   - Automate restore testing
   - Auto-cleanup old backups

## Troubleshooting

### Backup Job Fails

```bash
# Check job logs
kubectl logs job/<backup-job> -n mlops-platform

# Check pod events
kubectl describe job/<backup-job> -n mlops-platform

# Common issues:
# - Insufficient disk space: Increase PVC size
# - Permission denied: Check RBAC and IAM roles
# - Network timeout: Check network policies
```

### Restore Fails

```bash
# Verify backup file exists
aws s3 ls s3://mlops-platform-backups/backups/postgres/

# Test database connection
kubectl exec -it <postgres-pod> -n mlops-platform -- psql -U mlflow -c "SELECT 1"

# Check disk space
kubectl exec -it <postgres-pod> -n mlops-platform -- df -h
```

### S3 Upload Fails

```bash
# Verify IAM role
kubectl describe sa backup-sa -n mlops-platform

# Test AWS credentials
kubectl run aws-test --image=amazon/aws-cli -it --rm -- \
  sts get-caller-identity

# Check S3 bucket policy
aws s3api get-bucket-policy --bucket mlops-platform-backups
```

## References

- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)
- [Kubernetes CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Velero for Kubernetes Backup](https://velero.io/)
