# MLOps Platform - Step-by-Step Build 🚀

> **Learning Project**: Build a production-ready MLOps platform incrementally, one component at a time.

A hands-on guide to building a complete MLOps pipeline for customer churn prediction. Learn modern ML deployment practices by building each component from scratch.

## 🎯 What You'll Build

By the end of this project, you'll have a production-ready ML platform with:
- ✅ Machine learning model training pipeline
- ✅ REST API for model serving
- ✅ Automated testing and CI/CD
- ✅ Containerization with Docker
- ✅ Monitoring and observability
- ✅ Cloud deployment infrastructure

## 📚 Learning Path

### ✅ Phase 0: Project Setup (Current)
**Status**: In Progress  
**What we'll do**:
- [x] Initialize repository
- [ ] Create basic project structure
- [ ] Set up Python virtual environment
- [ ] Install initial dependencies

**Time**: 30 minutes

---

### 📦 Phase 1: Basic ML Model
**What you'll learn**: Core ML fundamentals, scikit-learn basics  
**What we'll build**:
- Simple customer churn dataset generator
- Train a basic Random Forest model
- Save and load models with joblib
- Basic command-line training script

**Files to create**: `src/train_simple.py`, `src/model_simple.py`

---

### 🔄 Phase 2: Data Pipeline
**What you'll learn**: Data preprocessing, feature engineering  
**What we'll build**:
- Data preprocessing functions
- Feature scaling and encoding
- Data validation checks
- Separate training and preprocessing logic

**Files to create**: `src/preprocessing.py`, `src/data_validation.py`

---

### 🎯 Phase 3: Enhanced Model Training
**What you'll learn**: Model evaluation, hyperparameter tuning  
**What we'll build**:
- Multiple model types (Random Forest, Gradient Boosting)
- Comprehensive evaluation metrics
- Model comparison
- Training configuration

**Files to create**: `src/model.py`, `src/train.py`, `config/config.yaml`

---

### 🌐 Phase 4: REST API
**What you'll learn**: FastAPI, API design, validation  
**What we'll build**:
- FastAPI application
- Prediction endpoint
- Input validation with Pydantic
- Auto-generated API docs
- Health check endpoint

**Files to create**: `src/api.py`, `src/schemas.py`

---

### 🧪 Phase 5: Testing
**What you'll learn**: Unit testing, pytest, test-driven development  
**What we'll build**:
- Unit tests for all components
- Test fixtures
- Coverage reporting
- Integration tests

**Files to create**: `tests/test_model.py`, `tests/test_api.py`, `tests/conftest.py`

---

### 🐳 Phase 6: Docker
**What you'll learn**: Containerization, Docker best practices  
**What we'll build**:
- Dockerfile for the application
- Docker Compose for local development
- Multi-container setup (API + database)
- Volume management

**Files to create**: `Dockerfile`, `docker-compose.yml`, `.dockerignore`

---

### 🔄 Phase 7: CI/CD
**What you'll learn**: GitHub Actions, automation, DevOps  
**What we'll build**:
- Automated testing pipeline
- Code quality checks (linting, formatting)
- Docker image building
- Pre-commit hooks

**Files to create**: `.github/workflows/ci.yml`, `.pre-commit-config.yaml`

---

### 📊 Phase 8: MLflow Integration
**What you'll learn**: Experiment tracking, model registry  
**What we'll build**:
- MLflow experiment tracking
- Model versioning
- Artifact logging
- MLflow UI setup

**Updates**: Modify `src/train.py` to add MLflow tracking

---

### 📈 Phase 9: Monitoring
**What you'll learn**: Observability, metrics, alerting  
**What we'll build**:
- Prometheus metrics
- Grafana dashboards
- Custom application metrics
- Alert rules

**Files to create**: `prometheus.yml`, `grafana/dashboards/`, monitoring configs

---

### ☸️ Phase 10: Cloud Deployment
**What you'll learn**: Kubernetes or AWS ECS, Infrastructure as Code  
**What we'll build**:
- Kubernetes manifests OR Terraform configs
- Load balancer setup
- Auto-scaling configuration
- Production deployment

**Files to create**: `k8s/` or `terraform/` directory with configs

---

## 🛠️ Tech Stack

Will be added incrementally:
- **Python 3.10+** (Phase 1)
- **Scikit-learn** (Phase 1)
- **Pandas & NumPy** (Phase 1)
- **FastAPI** (Phase 4)
- **Pytest** (Phase 5)
- **Docker** (Phase 6)
- **GitHub Actions** (Phase 7)
- **MLflow** (Phase 8)
- **Prometheus/Grafana** (Phase 9)
- **Kubernetes/Terraform** (Phase 10)

## 🎓 Learning Approach

Each phase will:
1. **Explain** the concept and why it matters
2. **Build** the component step by step
3. **Test** that it works
4. **Document** what you've learned

## 📝 Current Status

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
