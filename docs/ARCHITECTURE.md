# Architecture Overview

High-level architecture of the MLOps platform for churn prediction.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         External Users                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTPS
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    Ingress Controller                            │
│                   (NGINX + TLS/SSL)                             │
└────────────┬──────────────────┬──────────────────┬──────────────┘
             │                  │                  │
    ┌────────▼────────┐ ┌──────▼───────┐ ┌───────▼────────┐
    │   Churn API     │ │    MLflow    │ │    Grafana     │
    │   (FastAPI)     │ │    Server    │ │  (Monitoring)  │
    └────────┬────────┘ └──────┬───────┘ └───────┬────────┘
             │                  │                  │
             │          ┌───────▼────────┐        │
             │          │   PostgreSQL   │        │
             │          │  (Metadata DB) │        │
             │          └────────────────┘        │
             │                                     │
             │          ┌────────────────┐        │
             └─────────►│  MLflow Model  │        │
                        │    Registry    │        │
                        └────────────────┘        │
                                                   │
                        ┌────────────────┐        │
                        │   Prometheus   │◄───────┘
                        │  (Metrics DB)  │
                        └────────────────┘
```

## Component Details

### API Layer

#### Churn Prediction API
- **Technology**: FastAPI (Python 3.9)
- **Purpose**: RESTful API for churn predictions
- **Features**:
  - Single prediction endpoint
  - Batch prediction endpoint
  - Health checks
  - Prometheus metrics export
  - MLflow model registry integration
- **Scalability**: Horizontal pod autoscaling (2-10 replicas)
- **Resources**: 500m CPU, 512Mi RAM (request), 1 CPU, 1Gi RAM (limit)

### ML Platform

#### MLflow Server
- **Technology**: MLflow 2.9.2
- **Purpose**: Experiment tracking and model registry
- **Features**:
  - Experiment logging
  - Model versioning
  - Model stage management (Staging/Production)
  - Artifact storage
  - Metrics tracking
- **Storage**: 20Gi PVC for artifacts
- **Database**: PostgreSQL for metadata

#### PostgreSQL
- **Technology**: PostgreSQL 15 Alpine
- **Purpose**: Backend store for MLflow metadata
- **Storage**: 5Gi PVC
- **Backup**: Daily automated backups
- **Resources**: 250m CPU, 256Mi RAM (request), 500m CPU, 512Mi RAM (limit)

### Monitoring

#### Prometheus
- **Technology**: Prometheus 2.45
- **Purpose**: Metrics collection and alerting
- **Metrics Collected**:
  - HTTP request rates
  - Response latencies
  - Prediction counts
  - Model confidence scores
  - Resource usage
  - Custom business metrics
- **Retention**: 15 days
- **Storage**: 10Gi PVC

#### Grafana
- **Technology**: Grafana 10.0
- **Purpose**: Metrics visualization and dashboards
- **Dashboards**:
  - API Performance
  - Model Metrics
  - Infrastructure Health
  - Business KPIs
- **Data Sources**: Prometheus

#### Alertmanager
- **Purpose**: Alert routing and notification
- **Integrations**:
  - Slack notifications
  - Email alerts
  - PagerDuty (optional)
- **Alert Categories**:
  - Critical: Immediate response (< 15 min)
  - Warning: Response within 1 hour
  - Info: Informational only

### Security

#### Secrets Management
- **Kubernetes Secrets**: Development and testing
- **AWS Secrets Manager**: Production (recommended)
- **Secrets Store CSI Driver**: Integration with external secret stores
- **Rotation**: Quarterly automated rotation

#### Network Security
- **Network Policies**: Pod-level network segmentation
- **Ingress**: NGINX with TLS/SSL termination
- **Service Mesh**: (Optional) Istio for mTLS

#### Access Control
- **RBAC**: Role-based access control for Kubernetes resources
- **Pod Security Policies**: Restrict privileged containers
- **Service Accounts**: Dedicated accounts per service
- **IAM Roles**: AWS IAM roles for service accounts (IRSA)

### Backup & Recovery

#### Backup Strategy
- **PostgreSQL**: Daily full backups at 2 AM
- **MLflow Artifacts**: Daily backups at 3 AM
- **Retention**: 7 days local, 90 days in S3
- **Storage**: 50Gi PVC + S3 bucket

#### Disaster Recovery
- **RTO**: 4 hours (Recovery Time Objective)
- **RPO**: 24 hours (Recovery Point Objective)
- **Testing**: Quarterly DR drills
- **Documentation**: Complete restore procedures

## Data Flow

### Training Pipeline

```
1. Data Ingestion
   └─> Training Script (train.py)
       ├─> MLflow Experiment Tracking
       │   ├─> Log parameters
       │   ├─> Log metrics
       │   └─> Log artifacts
       └─> Model Registry
           ├─> Register model
           └─> Tag as Production/Staging
```

### Prediction Pipeline

```
1. Client Request
   └─> Ingress Controller
       └─> Churn API
           ├─> Load Model (from registry or local)
           ├─> Preprocessing
           ├─> Prediction
           ├─> Log metrics to Prometheus
           └─> Return result
```

### Monitoring Pipeline

```
1. Application Metrics
   └─> Prometheus (scrape every 15s)
       ├─> Evaluate alert rules
       │   └─> Alertmanager
       │       └─> Slack/Email notifications
       └─> Store time-series data
           └─> Grafana queries and visualizations
```

## Scalability

### Horizontal Scaling

- **API**: 2-10 replicas based on CPU utilization (70% threshold)
- **MLflow**: Single replica (stateful, consider HA setup for production)
- **PostgreSQL**: Single replica + read replicas (optional)
- **Prometheus**: Single replica (consider Thanos for HA)

### Vertical Scaling

- **Resource Limits**: Configurable per deployment
- **Storage**: PVCs support volume expansion
- **Database**: Can upgrade PostgreSQL instance size

### Load Balancing

- **Ingress**: NGINX load balancer
- **Service**: Kubernetes service with ClusterIP
- **Algorithm**: Round-robin distribution

## High Availability

### Current Setup
- Single replica for stateful services (PostgreSQL, MLflow)
- Multiple replicas for stateless services (API)
- PersistentVolumes with backup and restore

### Production Recommendations

1. **Database HA**:
   - PostgreSQL with streaming replication
   - Or use managed database (RDS, Cloud SQL)

2. **Multi-Zone Deployment**:
   - Spread pods across availability zones
   - Use pod anti-affinity rules

3. **Ingress HA**:
   - Multiple ingress controller replicas
   - Cross-zone load balancing

4. **Monitoring HA**:
   - Prometheus federation or Thanos
   - Grafana with shared database backend

## Performance

### Expected Performance

- **API Latency**: < 100ms (p95)
- **Throughput**: 100+ requests/second per replica
- **Model Load Time**: < 5 seconds
- **Training Time**: 2-5 minutes (sample data)

### Optimization Strategies

1. **Caching**: Redis for prediction caching
2. **Batching**: Batch predictions for efficiency
3. **Model Optimization**: Quantization, pruning
4. **Connection Pooling**: Database connections
5. **CDN**: Static assets via CDN

## Cost Optimization

### Resource Allocation

- **Over-provisioning**: Avoid setting limits too high
- **Right-sizing**: Monitor actual usage and adjust
- **Spot Instances**: Use for non-critical workloads
- **Storage Lifecycle**: S3 lifecycle policies for backups

### Cost Monitoring

- **Metrics**: Track cost per prediction
- **Alerts**: Budget alerts via cloud provider
- **Optimization**: Regular reviews and adjustments

## Security Layers

### Network Layer
- VPC with public/private subnets
- Security groups and network ACLs
- Network policies in Kubernetes
- WAF for ingress traffic (optional)

### Application Layer
- API key authentication
- Rate limiting
- Input validation
- Output sanitization

### Data Layer
- Encryption at rest (EBS, S3)
- Encryption in transit (TLS)
- Database encryption
- Backup encryption

### Identity Layer
- RBAC for Kubernetes
- IAM roles and policies
- Service account tokens
- Secrets management

## Deployment Environments

### Development
- Local Kubernetes (minikube, kind)
- Minimal resources
- Mock services allowed
- Frequent updates

### Staging
- Production-like environment
- Same configuration as prod
- Lower resource allocation
- Testing ground for releases

### Production
- Full resources
- High availability setup
- Strict change management
- Comprehensive monitoring

## Technology Stack

### Languages
- Python 3.9 (API, ML training)
- Bash (scripts, automation)

### Frameworks
- FastAPI (web framework)
- Scikit-learn (ML framework)
- MLflow (ML platform)

### Infrastructure
- Kubernetes 1.24+
- Docker (containerization)
- Terraform (IaC)
- Helm (package management)

### Cloud Services
- AWS EKS (Kubernetes)
- AWS S3 (backups, artifacts)
- AWS Secrets Manager (secrets)
- AWS Route53 (DNS)
- AWS ALB/NLB (load balancing)

### Monitoring
- Prometheus (metrics)
- Grafana (visualization)
- Alertmanager (alerting)

### CI/CD
- GitHub Actions (CI/CD)
- Docker Hub / ECR (registry)

## Future Enhancements

### Short Term (1-3 months)
- [ ] Model A/B testing
- [ ] Feature store integration
- [ ] Advanced monitoring (APM)
- [ ] Cost tracking dashboard

### Medium Term (3-6 months)
- [ ] Multi-model serving
- [ ] Real-time streaming predictions
- [ ] Advanced security (Vault, OIDC)
- [ ] Multi-region deployment

### Long Term (6-12 months)
- [ ] Auto-scaling ML training
- [ ] Advanced feature engineering pipeline
- [ ] Model drift detection
- [ ] Federated learning support

## References

- [Kubernetes Architecture](https://kubernetes.io/docs/concepts/architecture/)
- [MLflow Architecture](https://mlflow.org/docs/latest/tracking.html#tracking-server)
- [Prometheus Architecture](https://prometheus.io/docs/introduction/overview/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
