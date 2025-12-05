# Production Deployment Guide

Complete guide for deploying the MLOps platform to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Security Configuration](#security-configuration)
4. [Application Deployment](#application-deployment)
5. [Monitoring Setup](#monitoring-setup)
6. [Backup Configuration](#backup-configuration)
7. [Post-Deployment Validation](#post-deployment-validation)
8. [Maintenance](#maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- `kubectl` >= 1.24
- `terraform` >= 1.5
- `aws-cli` >= 2.0 (for AWS deployments)
- `helm` >= 3.0
- `git`
- `docker`

### Access Requirements

- Kubernetes cluster admin access
- Cloud provider credentials (AWS/GCP/Azure)
- Container registry access
- DNS management access
- SSL certificate for HTTPS

### Infrastructure Requirements

- **Kubernetes Cluster**: v1.24+
- **Nodes**: Minimum 3 worker nodes
- **Node Resources**: 4 CPU, 16GB RAM per node
- **Storage**: 200GB+ available for persistent volumes
- **Load Balancer**: For external traffic
- **Network**: VPC with private and public subnets

---

## Infrastructure Setup

### 1. Create Kubernetes Cluster

#### AWS EKS

```bash
cd terraform/

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Create cluster
terraform apply

# Configure kubectl
aws eks update-kubeconfig --name mlops-platform --region us-west-2
```

#### Verify Cluster

```bash
kubectl cluster-info
kubectl get nodes
kubectl version
```

### 2. Create Namespace

```bash
kubectl create namespace mlops-platform

# Set as default namespace
kubectl config set-context --current --namespace=mlops-platform
```

### 3. Configure Storage Classes

```bash
# For AWS EBS
cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
EOF
```

### 4. Install CSI Drivers

```bash
# AWS EBS CSI Driver
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=release-1.24"

# Verify
kubectl get pods -n kube-system | grep ebs-csi
```

---

## Security Configuration

### 1. Create Secrets

**Generate strong passwords:**

```bash
# PostgreSQL password
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# MLflow credentials
MLFLOW_PASSWORD=$(openssl rand -base64 32)

# API key
API_KEY=$(openssl rand -hex 32)
```

**Create secrets in Kubernetes:**

```bash
# PostgreSQL secrets
kubectl create secret generic postgres-secrets \
  --from-literal=postgres-user=mlflow \
  --from-literal=postgres-password="${POSTGRES_PASSWORD}" \
  --from-literal=postgres-db=mlflow \
  -n mlops-platform

# MLflow secrets
kubectl create secret generic mlflow-secrets \
  --from-literal=db-username=mlflow \
  --from-literal=db-password="${POSTGRES_PASSWORD}" \
  -n mlops-platform

# API secrets
kubectl create secret generic api-secrets \
  --from-literal=api-key="${API_KEY}" \
  -n mlops-platform
```

**For production, use AWS Secrets Manager:**

```bash
# Store in AWS Secrets Manager
aws secretsmanager create-secret \
  --name mlops-platform/postgres/credentials \
  --secret-string "{\"username\":\"mlflow\",\"password\":\"${POSTGRES_PASSWORD}\",\"database\":\"mlflow\"}"

aws secretsmanager create-secret \
  --name mlops-platform/api/key \
  --secret-string "{\"api-key\":\"${API_KEY}\"}"

# Deploy Secrets Store CSI Driver
kubectl apply -f secrets/aws-secret-provider.yaml
```

### 2. Apply RBAC Policies

```bash
kubectl apply -f security/rbac.yaml
kubectl apply -f security/pod-security-policy.yaml
```

### 3. Configure Network Policies

```bash
kubectl apply -f security/network-policies.yaml
```

### 4. Set Resource Quotas

```bash
kubectl apply -f security/resource-quotas.yaml
kubectl apply -f security/pod-disruption-budgets.yaml
```

### 5. Enable Encryption

**Kubernetes secrets encryption at rest:**

```bash
# Create encryption config
cat > encryption-config.yaml <<EOF
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: $(head -c 32 /dev/urandom | base64)
      - identity: {}
EOF

# Apply to cluster (method varies by Kubernetes distribution)
# For EKS, use KMS: https://docs.aws.amazon.com/eks/latest/userguide/enable-kms.html
```

---

## Application Deployment

### 1. Deploy PostgreSQL

```bash
kubectl apply -f mlflow/postgres-deployment.yaml

# Wait for ready
kubectl wait --for=condition=ready pod -l app=mlflow-postgres --timeout=300s

# Verify
kubectl exec -it deployment/mlflow-postgres -- psql -U mlflow -c "SELECT 1"
```

### 2. Deploy MLflow Server

```bash
kubectl apply -f mlflow/mlflow-config.yaml
kubectl apply -f mlflow/mlflow-deployment.yaml
kubectl apply -f mlflow/mlflow-service.yaml

# Wait for ready
kubectl wait --for=condition=ready pod -l app=mlflow-server --timeout=300s

# Test MLflow
kubectl port-forward svc/mlflow-server 5000:5000 &
curl http://localhost:5000/health
```

### 3. Train Initial Model

```bash
# Create training job
kubectl create job model-training --image=<your-registry>/churn-model:latest -- python src/train.py

# Monitor training
kubectl logs job/model-training -f

# Verify model in MLflow
curl http://localhost:5000/api/2.0/mlflow/registered-models/list
```

### 4. Deploy API

```bash
# Build and push image
docker build -t <your-registry>/churn-api:latest .
docker push <your-registry>/churn-api:latest

# Update image in deployment
kubectl set image deployment/churn-api api=<your-registry>/churn-api:latest

# Or apply deployment
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Wait for ready
kubectl wait --for=condition=ready pod -l app=churn-api --timeout=300s

# Test API
kubectl port-forward svc/churn-api 8000:8000 &
curl http://localhost:8000/health
```

### 5. Configure Ingress

```bash
# Install ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/aws/deploy.yaml

# Create SSL certificate
# Option 1: Use cert-manager with Let's Encrypt
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Option 2: Upload existing certificate
kubectl create secret tls mlops-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key

# Create ingress
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mlops-ingress
  namespace: mlops-platform
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.mlops.example.com
    - mlflow.mlops.example.com
    - grafana.mlops.example.com
    secretName: mlops-tls
  rules:
  - host: api.mlops.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: churn-api
            port:
              number: 8000
  - host: mlflow.mlops.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mlflow-server
            port:
              number: 5000
  - host: grafana.mlops.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: grafana
            port:
              number: 3000
EOF
```

### 6. Configure DNS

```bash
# Get load balancer address
kubectl get ingress mlops-ingress -n mlops-platform

# Create DNS records (example with AWS Route53)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789ABC \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.mlops.example.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "<loadbalancer-dns>"}]
      }
    }]
  }'
```

---

## Monitoring Setup

### 1. Deploy Prometheus

```bash
kubectl apply -f monitoring/prometheus-config.yaml
kubectl apply -f monitoring/prometheus-alerts.yaml
kubectl apply -f monitoring/prometheus-deployment.yaml
kubectl apply -f monitoring/prometheus-service.yaml

# Verify
kubectl wait --for=condition=ready pod -l app=prometheus --timeout=300s
```

### 2. Deploy Grafana

```bash
kubectl apply -f monitoring/grafana-datasource.yaml
kubectl apply -f monitoring/grafana-dashboards-config.yaml
kubectl apply -f monitoring/grafana-dashboards.yaml
kubectl apply -f monitoring/grafana-deployment.yaml
kubectl apply -f monitoring/grafana-service.yaml

# Get Grafana admin password
kubectl get secret grafana -o jsonpath="{.data.admin-password}" | base64 -d
```

### 3. Configure Alertmanager

```bash
# Create Alertmanager config
kubectl create configmap alertmanager-config \
  --from-file=alertmanager.yml=monitoring/alertmanager-config.yaml

# Deploy Alertmanager
kubectl apply -f monitoring/alertmanager-deployment.yaml
```

### 4. Configure Alert Channels

**Slack integration:**

```yaml
# Add to alertmanager-config.yaml
receivers:
- name: 'slack'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    channel: '#mlops-alerts'
    title: '{{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

**Email integration:**

```yaml
receivers:
- name: 'email'
  email_configs:
  - to: 'team@example.com'
    from: 'alerts@example.com'
    smarthost: 'smtp.gmail.com:587'
    auth_username: 'alerts@example.com'
    auth_password: '<password>'
```

---

## Backup Configuration

### 1. Create S3 Bucket

```bash
# Create bucket
aws s3 mb s3://mlops-platform-backups-prod

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket mlops-platform-backups-prod \
  --versioning-configuration Status=Enabled

# Set lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket mlops-platform-backups-prod \
  --lifecycle-configuration file://backup/s3-lifecycle.json

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket mlops-platform-backups-prod \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "<kms-key-id>"
      }
    }]
  }'
```

### 2. Create IAM Role for Backups

```bash
# Create policy
aws iam create-policy \
  --policy-name MLOpsBackupPolicy \
  --policy-document file://backup/backup-policy.json

# Create service account with IAM role
eksctl create iamserviceaccount \
  --name backup-sa \
  --namespace mlops-platform \
  --cluster mlops-platform \
  --attach-policy-arn arn:aws:iam::<account>:policy/MLOpsBackupPolicy \
  --approve
```

### 3. Deploy Backup CronJobs

```bash
# Update S3 bucket name in backup-cronjobs.yaml
sed -i 's/mlops-platform-backups/mlops-platform-backups-prod/g' backup/backup-cronjobs.yaml

# Deploy
kubectl apply -f backup/backup-cronjobs.yaml

# Verify CronJobs
kubectl get cronjobs -n mlops-platform

# Test backup manually
kubectl create job --from=cronjob/postgres-backup postgres-backup-test
kubectl logs job/postgres-backup-test -f
```

---

## Post-Deployment Validation

### 1. Health Checks

```bash
# Check all pods
kubectl get pods -n mlops-platform

# Check services
kubectl get svc -n mlops-platform

# Check ingress
kubectl get ingress -n mlops-platform

# Test API health
curl https://api.mlops.example.com/health

# Test MLflow health
curl https://mlflow.mlops.example.com/health

# Test Grafana
curl https://grafana.mlops.example.com/api/health
```

### 2. Functional Tests

```bash
# Test prediction endpoint
curl -X POST https://api.mlops.example.com/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "account_length": 100,
    "voice_mail_plan": 1,
    "voice_mail_messages": 5,
    "day_mins": 150.5,
    "day_calls": 80,
    "evening_mins": 200.0,
    "evening_calls": 100,
    "night_mins": 180.0,
    "night_calls": 90,
    "international_plan": 0,
    "international_mins": 10.0,
    "international_calls": 3,
    "customer_service_calls": 1
  }'

# Test batch prediction
curl -X POST https://api.mlops.example.com/predict/batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d @test-data.json
```

### 3. Load Testing

```bash
# Install k6
brew install k6  # or appropriate package manager

# Create load test script
cat > load-test.js <<EOF
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '5m', target: 200 },
    { duration: '2m', target: 0 },
  ],
};

export default function () {
  let payload = JSON.stringify({
    account_length: 100,
    voice_mail_plan: 1,
    // ... other fields
  });

  let params = {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': '${API_KEY}',
    },
  };

  let res = http.post('https://api.mlops.example.com/predict', payload, params);
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 2s': (r) => r.timings.duration < 2000,
  });

  sleep(1);
}
EOF

# Run load test
k6 run load-test.js
```

### 4. Monitor Metrics

```bash
# Port-forward to Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n mlops-platform &

# Check targets are up
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job:.labels.job, health:.health}'

# Check for alerts
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts'

# View in Grafana
kubectl port-forward svc/grafana 3000:3000 -n mlops-platform &
open http://localhost:3000
```

### 5. Verify Backups

```bash
# Check backup jobs ran
kubectl get jobs -n mlops-platform | grep backup

# Check S3 backups exist
aws s3 ls s3://mlops-platform-backups-prod/backups/ --recursive

# Test restore (in test namespace)
kubectl create namespace dr-test
# Follow restore procedure from backup/README.md
```

---

## Maintenance

### Regular Tasks

#### Daily
- Check alert inbox
- Review error logs
- Monitor resource usage

#### Weekly
- Review capacity trends
- Check backup success rate
- Update dependencies

#### Monthly
- Test disaster recovery
- Review and rotate secrets
- Update security patches
- Capacity planning review

#### Quarterly
- Full DR drill
- Security audit
- Performance optimization
- Cost optimization review

### Updating the Application

```bash
# 1. Build new image
docker build -t <registry>/churn-api:v2.0.0 .
docker push <registry>/churn-api:v2.0.0

# 2. Update deployment
kubectl set image deployment/churn-api \
  api=<registry>/churn-api:v2.0.0 \
  -n mlops-platform

# 3. Monitor rollout
kubectl rollout status deployment/churn-api -n mlops-platform

# 4. Verify
curl https://api.mlops.example.com/health

# 5. If issues, rollback
kubectl rollout undo deployment/churn-api -n mlops-platform
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment churn-api --replicas=5 -n mlops-platform

# Enable autoscaling
kubectl autoscale deployment churn-api \
  --min=2 \
  --max=10 \
  --cpu-percent=70 \
  -n mlops-platform

# Check HPA status
kubectl get hpa -n mlops-platform
```

### Rotating Secrets

```bash
# 1. Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)

# 2. Update secret
kubectl create secret generic postgres-secrets \
  --from-literal=postgres-password="${NEW_PASSWORD}" \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Update database password
kubectl exec -it deployment/mlflow-postgres -- \
  psql -U mlflow -c "ALTER USER mlflow WITH PASSWORD '${NEW_PASSWORD}';"

# 4. Restart dependent services
kubectl rollout restart deployment/mlflow-server -n mlops-platform
```

---

## Troubleshooting

See [Runbooks](../runbooks/README.md) for detailed troubleshooting procedures.

### Quick Diagnostics

```bash
# Check all resources
kubectl get all -n mlops-platform

# Check events
kubectl get events -n mlops-platform --sort-by='.lastTimestamp'

# Check logs
kubectl logs -l app=churn-api -n mlops-platform --tail=100

# Check resource usage
kubectl top pods -n mlops-platform
kubectl top nodes
```

### Common Issues

**Pods not starting**: Check resource constraints, PVC availability, and image pull errors

**High latency**: Scale up replicas, increase resource limits, check for slow dependencies

**Data loss**: Restore from backup, verify PVC retention policy

**Certificate errors**: Renew SSL certificates, check cert-manager logs

---

## Security Checklist

- [ ] Secrets stored securely (not in Git)
- [ ] RBAC policies applied
- [ ] Network policies configured
- [ ] Pod security policies enabled
- [ ] Resource quotas set
- [ ] Ingress has SSL/TLS
- [ ] Database encrypted at rest
- [ ] Backups encrypted
- [ ] Audit logging enabled
- [ ] Security scanning in CI/CD

---

## References

- [Kubernetes Production Best Practices](https://kubernetes.io/docs/setup/best-practices/)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [MLflow Production Guide](https://mlflow.org/docs/latest/production.html)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)

## Support

- Documentation: `/docs`
- Runbooks: `/runbooks`
- Issues: GitHub Issues
- Contact: team@example.com
