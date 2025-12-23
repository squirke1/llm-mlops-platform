# MLOps Platform - Production-Ready Customer Churn Prediction 

> **Complete MLOps Platform**: Production-grade machine learning system with experiment tracking, monitoring, and automated operations.

A comprehensive MLOps platform for customer churn prediction built with modern ML engineering practices. Includes MLflow for experiment tracking, Prometheus/Grafana for monitoring, automated backups, and production-hardened security.

##  What's Included

This production-ready ML platform features:
-  Machine learning model training pipeline with MLflow tracking
-  REST API for model serving (FastAPI)
-  Automated testing and CI/CD (GitHub Actions)
-  Containerization with Docker and Kubernetes orchestration
-  Monitoring and observability (Prometheus + Grafana)
-  MLflow experiment tracking and model registry
-  Automated backup and disaster recovery
-  Production security hardening
-  Cloud deployment infrastructure (Terraform)
-  Model A/B testing with traffic routing and metrics
-  Feature Store with Feast for centralized feature management

##  Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system architecture.

**Key Components**:
- **API Layer**: FastAPI with prediction endpoints and health checks
- **ML Platform**: MLflow for experiment tracking and model registry
- **Storage**: PostgreSQL for metadata, PVCs for artifacts
- **Monitoring**: Prometheus metrics + Grafana dashboards + Alertmanager
- **Security**: Kubernetes RBAC, network policies, secrets management
- **Backup**: Automated daily backups to S3 with restore procedures

##  Learning Path

###  Phase 0: Project Setup (Current)
**Status**: In Progress  
**What we'll do**:
- [x] Initialize repository
- [ ] Create basic project structure
- [ ] Set up Python virtual environment
- [ ] Install initial dependencies

**Time**: 30 minutes

---

###  Phase 1: Basic ML Model
**What you'll learn**: Core ML fundamentals, scikit-learn basics  
**What we'll build**:
- Simple customer churn dataset generator
- Train a basic Random Forest model
- Save and load models with joblib
- Basic command-line training script

**Files to create**: `src/train_simple.py`, `src/model_simple.py`

---

###  Phase 2: Data Pipeline
**What you'll learn**: Data preprocessing, feature engineering  
**What we'll build**:
- Data preprocessing functions
- Feature scaling and encoding
- Data validation checks
- Separate training and preprocessing logic

**Files to create**: `src/preprocessing.py`, `src/data_validation.py`

---

###  Phase 3: Enhanced Model Training
**What you'll learn**: Model evaluation, hyperparameter tuning  
**What we'll build**:
- Multiple model types (Random Forest, Gradient Boosting)
- Comprehensive evaluation metrics
- Model comparison
- Training configuration

**Files to create**: `src/model.py`, `src/train.py`, `config/config.yaml`

---

###  Phase 4: REST API
**What you'll learn**: FastAPI, API design, validation  
**What we'll build**:
- FastAPI application
- Prediction endpoint
- Input validation with Pydantic
- Auto-generated API docs
- Health check endpoint

**Files to create**: `src/api.py`, `src/schemas.py`

---

###  Phase 5: Testing
**What you'll learn**: Unit testing, pytest, test-driven development  
**What we'll build**:
- Unit tests for all components
- Test fixtures
##  Quick Start

### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- kubectl (for Kubernetes deployment)
- AWS CLI (for cloud deployment)

### Local Development

```bash
# Clone repository
git clone https://github.com/squirke1/llm-mlops-platform.git
cd llm-mlops-platform

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Train model
python src/train.py

# Run API locally
uvicorn api.app:app --reload

# Run tests
pytest tests/ -v

# Start with Docker Compose
docker-compose up
```

### Production Deployment

See [docs/PRODUCTION_DEPLOYMENT.md](docs/PRODUCTION_DEPLOYMENT.md) for complete production deployment guide.

##  Tech Stack

- **Languages**: Python 3.9
- **ML Framework**: Scikit-learn 1.3.2
- **API Framework**: FastAPI 0.104.1
- **Experiment Tracking**: MLflow 2.9.2
- **Database**: PostgreSQL 15
- **Monitoring**: Prometheus 2.45 + Grafana 10.0
- **Testing**: Pytest 7.4.3
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes 1.24+
- **CI/CD**: GitHub Actions
- **Infrastructure**: Terraform (AWS EKS)

##  Development Phases

###  Phase 1-6: Core ML Pipeline (Completed)
- ML model training and evaluation
- REST API with FastAPI
- Comprehensive testing
- Docker containerization

###  Phase 7: CI/CD (Completed)
- Automated testing pipeline
- Code quality checks (black, isort, flake8)
- Docker image building
- Kubernetes manifest validation
- Terraform validation

###  Phase 8: Monitoring (Completed)
- Prometheus metrics collection
- Grafana dashboards
- Custom application metrics
- Alert rules
- API instrumentation

###  Phase 9: MLflow Integration (Completed)
- Experiment tracking
- Model registry with versioning
- Model stage management (Production/Staging)
- Artifact storage
- API integration with model registry

###  Phase 10: Production Hardening (Completed)
- **Secrets Management**: Kubernetes secrets + AWS Secrets Manager integration
- **Security Hardening**: RBAC, network policies, pod security policies
- **Backup & DR**: Automated daily backups to S3, restore procedures
- **Monitoring & Alerts**: Comprehensive alerting rules and runbooks
- **Documentation**: Production deployment guide, architecture docs, runbooks

###  Phase 11: Model A/B Testing (Completed)
- **Variant Management**: Support for multiple model versions in production
- **Routing Strategies**: Random, hash-based (user_id), and sticky (session_id)
- **Traffic Control**: Dynamic traffic splitting between model variants
- **Metrics Tracking**: Per-variant performance metrics (latency, errors, requests)
- **Gradual Rollout**: Canary deployments and progressive traffic migration
- **Grafana Dashboard**: Visualizations for A/B test comparison
- **Documentation**: Complete A/B testing guide with examples

###  Phase 12: Feature Store Integration (Completed)
- **Feast Integration**: Production-ready feature store with online/offline serving
- **Feature Repository**: Defined feature views (behavior, demographics, contract)
- **Feature Services**: Training (v1) and online serving feature sets
- **On-Demand Features**: Derived feature calculations (ratios, averages)
- **API Integration**: Feature-enriched prediction endpoints
- **Training Integration**: Load features directly in training pipeline
- **Automated Materialization**: Kubernetes CronJob for feature sync (every 6 hours)
- **Multi-Environment**: SQLite (dev) and S3/DynamoDB (production)
- **Documentation**: Comprehensive feature store guide

##  Project Structure

```
llm-mlops-platform/
 api/                        # FastAPI application
    app.py                 # API endpoints and model serving
    schemas.py             # Pydantic schemas
    ab_testing.py          # A/B testing logic
 feature_store/             # Feature store (Feast)
    feature_repo.py       # Feature definitions
    feature_store.yaml    # Feast configuration
    feature_store_client.py # Feature store client
    generate_features.py  # Data generation
    setup_feature_store.py # Initialization
 src/                       # Source code
    data.py               # Data generation
    model.py              # Model training logic
    train.py              # Training script with MLflow
    mlflow_utils.py       # MLflow utilities
 tests/                     # Test suite
    test_api.py           # API tests
    test_model.py         # Model tests
    test_ab_testing.py    # A/B testing tests
    test_feature_store.py # Feature store tests
    conftest.py           # Test fixtures
 k8s/                       # Kubernetes manifests
    deployment.yaml       # API deployment
    service.yaml          # API service
    namespace.yaml        # Namespace definition
    ab-testing-config.yaml # A/B testing configuration
    feature-store.yaml    # Feature store deployment
 mlflow/                    # MLflow configuration
    mlflow-deployment.yaml
    postgres-deployment.yaml
    README.md
 monitoring/                # Monitoring setup
    prometheus-config.yaml
    prometheus-alerts.yaml
    grafana-dashboards.yaml
    dashboards/
       ab-testing-dashboard.json
    README.md
 security/                  # Security configurations
    rbac.yaml             # Role-based access control
    network-policies.yaml # Network segmentation
    pod-security-policy.yaml
    resource-quotas.yaml
 secrets/                   # Secrets management
    secrets.yaml          # Templates (not actual secrets)
    aws-secret-provider.yaml
    README.md
 backup/                    # Backup and DR
    backup-cronjobs.yaml  # Automated backup jobs
    README.md
 runbooks/                  # Operational runbooks
    README.md             # Incident response procedures
 docs/                      # Documentation
    ARCHITECTURE.md       # System architecture
    PRODUCTION_DEPLOYMENT.md
    AB_TESTING.md         # A/B testing guide
    FEATURE_STORE.md      # Feature store guide
 .github/workflows/         # CI/CD pipelines
    ci.yml
 Dockerfile                 # Container image
 docker-compose.yml         # Local development
 requirements.txt           # Python dependencies
 README.md                  # This file
```

##  Documentation

- **[Architecture](docs/ARCHITECTURE.md)**: System design and component details
- **[Production Deployment](docs/PRODUCTION_DEPLOYMENT.md)**: Complete deployment guide
- **[A/B Testing](docs/AB_TESTING.md)**: Model variant testing and gradual rollout
- **[Feature Store](docs/FEATURE_STORE.md)**: Feature management and serving
- **[Runbooks](runbooks/README.md)**: Operational procedures and troubleshooting
- **[MLflow Guide](mlflow/README.md)**: Experiment tracking and model registry
- **[Monitoring Guide](monitoring/README.md)**: Metrics and alerting
- **[Backup Guide](backup/README.md)**: Backup and disaster recovery
- **[Secrets Management](secrets/README.md)**: Security and secrets handling

##  API Endpoints

### Prediction Endpoints
- `POST /api/v1/predict` - Single prediction (supports user_id and session_id for A/B testing)
- `POST /api/v1/predict/features` - Feature store-enriched prediction (requires customer_id)
- `POST /predict/batch` - Batch predictions

### A/B Testing
- `GET /api/v1/ab-test/status` - Get A/B test configuration and variant stats

### Health & Monitoring
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

### API Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

##  Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov=api --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run with specific markers
pytest tests/ -m "not slow" -v
```

##  Monitoring

### Metrics Available
- HTTP request rates and latencies
- Prediction counts and results
- Model confidence scores
- A/B test variant performance (per-variant requests, latency, errors)
- Resource usage (CPU, memory)
- Business metrics (churn rate)

### Access Monitoring

```bash
# Port-forward Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n mlops-platform

# Port-forward Grafana
kubectl port-forward svc/grafana 3000:3000 -n mlops-platform
# Default credentials: admin / (see secret)
```

##  Security

### Features
- Kubernetes RBAC for access control
- Network policies for pod isolation
- Pod security policies
- Secrets management (K8s secrets / AWS Secrets Manager)
- TLS/SSL for all external traffic
- Resource quotas and limits
- Automated security scanning in CI

### Best Practices
- No secrets in Git
- Principle of least privilege
- Regular secret rotation
- Encrypted backups
- Audit logging enabled

##  Backup & Recovery

### Automated Backups
- **PostgreSQL**: Daily at 2 AM UTC
- **MLflow Artifacts**: Daily at 3 AM UTC
- **Retention**: 7 days local, 90 days in S3

### Disaster Recovery
- RTO: 4 hours
- RPO: 24 hours
- Quarterly DR drills
- Documented restore procedures

##  Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Workflow
- All PRs require passing CI checks
- Code coverage must be maintained (>80%)
- Follow existing code style (black, isort, flake8)
- Update documentation as needed

##  Status

**All phases completed!** 

This is a fully functional, production-ready MLOps platform with:
- Complete ML pipeline from training to serving
- Experiment tracking and model versioning with MLflow
- Comprehensive monitoring and alerting
- Production-grade security and backup solutions
- Full documentation and operational runbooks

Ready for deployment to production environments.

##  Contact

- **Author**: Stephen Quirke
- **Repository**: [github.com/squirke1/llm-mlops-platform](https://github.com/squirke1/llm-mlops-platform)
- **Issues**: [GitHub Issues](https://github.com/squirke1/llm-mlops-platform/issues)

##  License

**Phase 0**: Setting up the project foundation

**Next Steps**:
1. Create basic directory structure
2. Set up Python virtual environment
3. Install scikit-learn and pandas
4. Ready for Phase 1!

---

**Repository**: [llm-mlops-platform](https://github.com/squirke1/llm-mlops-platform)  
**Author**: Stephen Quirke  
**Purpose**: Educational MLOps showcase built incrementally
