# MLOps Platform Architecture Diagrams

This document provides visual diagrams of the complete MLOps platform architecture, data flows, and system components.

## Table of Contents
1. [High-Level System Architecture](#high-level-system-architecture)
2. [Data Pipeline Flow](#data-pipeline-flow)
3. [Feature Store Architecture](#feature-store-architecture)
4. [Model Training Pipeline](#model-training-pipeline)
5. [Prediction Service Architecture](#prediction-service-architecture)
6. [A/B Testing Flow](#ab-testing-flow)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Kubernetes Deployment](#kubernetes-deployment)
9. [Monitoring and Observability](#monitoring-and-observability)
10. [AWS Cloud Infrastructure](#aws-cloud-infrastructure)

---

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MLOps Platform - Complete System                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  External    │         │   External   │         │   GitHub     │
│  Users/Apps  │────────▶│   Ingress    │         │   (CI/CD)    │
│              │         │  (NGINX/ALB) │         │              │
└──────────────┘         └──────┬───────┘         └──────┬───────┘
                                │                         │
                                │                         ▼
                         ┌──────▼──────────────────────────────────┐
                         │    Kubernetes Cluster (EKS)             │
                         │                                         │
                         │  ┌─────────────────────────────┐       │
                         │  │   FastAPI Service Pods      │       │
                         │  │   (3-10 replicas)           │       │
                         │  │   - Model Serving           │       │
                         │  │   - A/B Testing Logic       │       │
                         │  │   - Feature Enrichment      │       │
                         │  └──────┬──────────────────────┘       │
                         │         │                               │
                         │         ▼                               │
                         │  ┌─────────────────────────────┐       │
                         │  │   Feature Store (Feast)     │       │
                         │  │   - Online Store (Redis)    │       │
                         │  │   - Offline Store (S3)      │       │
                         │  └─────────────────────────────┘       │
                         │                                         │
                         └─────────────────────────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
            ┌───────────────┐   ┌───────────────┐   ┌──────────────┐
            │   MLflow      │   │  Prometheus   │   │  PostgreSQL  │
            │   Tracking    │   │  Monitoring   │   │  Database    │
            │   Server      │   │               │   │              │
            └───────┬───────┘   └───────┬───────┘   └──────────────┘
                    │                   │
                    ▼                   ▼
            ┌───────────────┐   ┌───────────────┐
            │  S3 Storage   │   │    Grafana    │
            │  - Models     │   │  Dashboards   │
            │  - Artifacts  │   │               │
            └───────────────┘   └───────────────┘
```

---

## Data Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Data Pipeline Flow                               │
└─────────────────────────────────────────────────────────────────────────┘

1. DATA INGESTION
   ┌──────────────┐
   │  Raw Data    │
   │  Sources     │
   │  - CSV       │
   │  - Database  │
   │  - APIs      │
   └──────┬───────┘
          │
          ▼
   ┌──────────────────────┐
   │  Data Validation     │
   │  - Schema Check      │
   │  - Quality Rules     │
   │  - Outlier Detection │
   └──────┬───────────────┘
          │
          ▼

2. FEATURE ENGINEERING
   ┌──────────────────────┐
   │  Preprocessing       │
   │  - Encoding          │
   │  - Scaling           │
   │  - Imputation        │
   └──────┬───────────────┘
          │
          ▼
   ┌──────────────────────┐
   │  Feature Store       │
   │  (Feast)             │
   │  - Feature Registry  │
   │  - Versioning        │
   └──────┬───────────────┘
          │
          ├──────────────┬──────────────┐
          │              │              │
          ▼              ▼              ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ Offline  │   │ Training │   │  Online  │
   │  Store   │──▶│ Pipeline │   │  Store   │
   │  (S3)    │   │          │   │ (Redis)  │
   └──────────┘   └──────────┘   └────┬─────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │  API Serving    │
                              │  (Real-time)    │
                              └─────────────────┘
```

---

## Feature Store Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Feature Store (Feast) Architecture                    │
└─────────────────────────────────────────────────────────────────────────┘

                        ┌──────────────────────┐
                        │  Feature Repository  │
                        │  (Python Definitions)│
                        └──────────┬───────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
         ┌─────────────────┐  ┌────────────┐  ┌─────────────┐
         │ Feature Views   │  │  Entities  │  │   Sources   │
         │ - Behavior      │  │ - Customer │  │ - Parquet   │
         │ - Demographics  │  │            │  │ - S3        │
         │ - Contract      │  │            │  │             │
         └────────┬────────┘  └────────────┘  └─────────────┘
                  │
                  │
       ┌──────────┴──────────┐
       │                     │
       ▼                     ▼
┌──────────────┐      ┌──────────────┐
│ Offline      │      │   Online     │
│ Store (S3)   │      │ Store (Redis)│
│              │      │              │
│ Historical   │      │ Real-time    │
│ Features for │      │ Features for │
│ Training     │      │ Inference    │
└──────┬───────┘      └──────┬───────┘
       │                     │
       │                     │
       ▼                     ▼
┌──────────────┐      ┌──────────────┐
│   Training   │      │     API      │
│   Pipeline   │      │   Serving    │
│              │      │              │
│  get_        │      │  get_        │
│  historical_ │      │  online_     │
│  features()  │      │  features()  │
└──────────────┘      └──────────────┘

Materialization Pipeline (CronJob):
┌────────────────────────────────────────────┐
│  Every 6 hours:                            │
│  1. Read from Offline Store (S3)          │
│  2. Compute features                       │
│  3. Write to Online Store (Redis)         │
│  4. Update metadata                        │
└────────────────────────────────────────────┘
```

---

## Model Training Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Model Training Pipeline (MLflow)                    │
└─────────────────────────────────────────────────────────────────────────┘

START
  │
  ▼
┌──────────────────────┐
│ 1. Data Loading      │
│    - Feature Store   │
│    - get_historical  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 2. Preprocessing     │
│    - Encoding        │
│    - Scaling         │
│    - Split (80/20)   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐       ┌─────────────────────────┐
│ 3. Model Training    │──────▶│  MLflow Tracking        │
│    - Random Forest   │       │  - Log Parameters       │
│    - Fit on X_train  │       │  - Log Metrics          │
└──────┬───────────────┘       │  - Log Model            │
       │                       │  - Log Artifacts        │
       ▼                       └─────────────────────────┘
┌──────────────────────┐                 │
│ 4. Evaluation        │                 │
│    - Accuracy        │                 ▼
│    - Precision       │       ┌─────────────────────────┐
│    - Recall          │       │   MLflow Registry       │
│    - Confusion Matrix│       │   - Register Model      │
└──────┬───────────────┘       │   - Version: v1, v2..   │
       │                       │   - Stage: Staging      │
       ▼                       └───────┬─────────────────┘
┌──────────────────────┐               │
│ 5. Model Validation  │               │
│    - Metrics > Thresh│               │
│    - Business Rules  │               │
└──────┬───────────────┘               │
       │                               │
       │ Pass                          │
       ▼                               │
┌──────────────────────┐               │
│ 6. Promote to        │◀──────────────┘
│    Production Stage  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ 7. Deploy to API     │
│    - Load Model      │
│    - Update Endpoint │
└──────────────────────┘
  │
  ▼
END

Experiment Tracking Details:
┌─────────────────────────────────────┐
│ Each Run Captures:                  │
│ - Parameters (n_estimators, depth)  │
│ - Metrics (accuracy, precision)     │
│ - Artifacts (model.pkl, plots)      │
│ - Tags (team, environment)          │
│ - Git commit SHA                    │
│ - Timestamp                         │
└─────────────────────────────────────┘
```

---

## Prediction Service Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Prediction Service (FastAPI)                          │
└─────────────────────────────────────────────────────────────────────────┘

Client Request
     │
     ▼
┌─────────────────────┐
│  API Gateway        │
│  /api/v1/predict    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────┐
│  Request Validation             │
│  (Pydantic Schema)              │
│  - tenure_months: int           │
│  - monthly_charges: float       │
│  - contract_type: str           │
└─────────┬───────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│  A/B Test Variant Selection     │
│  - Hash user_id                 │
│  - Check traffic split          │
│  - Select model variant         │
└─────────┬───────────────────────┘
          │
          ├──────────────┬──────────────┐
          │              │              │
          ▼              ▼              ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ Model A │    │ Model B │    │ Model C │
    │  (80%)  │    │  (15%)  │    │  (5%)   │
    │ v1.0.0  │    │ v1.1.0  │    │ v2.0.0  │
    └────┬────┘    └────┬────┘    └────┬────┘
         │              │              │
         └──────────────┴──────────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │  Feature Enrichment    │
           │  (Optional)            │
           │  - Query Feature Store │
           │  - Merge with request  │
           └────────┬───────────────┘
                    │
                    ▼
           ┌────────────────────────┐
           │  Model Inference       │
           │  - predict()           │
           │  - predict_proba()     │
           └────────┬───────────────┘
                    │
                    ▼
           ┌────────────────────────┐
           │  Post-Processing       │
           │  - Format response     │
           │  - Add metadata        │
           └────────┬───────────────┘
                    │
                    ▼
           ┌────────────────────────┐
           │  Metrics Collection    │
           │  - Prometheus counters │
           │  - Latency histogram   │
           │  - Variant tracking    │
           └────────┬───────────────┘
                    │
                    ▼
           ┌────────────────────────┐
           │  Response              │
           │  {                     │
           │    prediction: 1       │
           │    probability: 0.73   │
           │    variant: "A"        │
           │  }                     │
           └────────────────────────┘
                    │
                    ▼
            Client Response
```

---

## A/B Testing Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         A/B Testing Architecture                         │
└─────────────────────────────────────────────────────────────────────────┘

Configuration:
┌──────────────────────────────────────────────────────┐
│  variants:                                           │
│    - name: "production"                              │
│      version: "1.0.0"                                │
│      traffic: 70.0                                   │
│    - name: "candidate_v2"                            │
│      version: "2.0.0"                                │
│      traffic: 20.0                                   │
│    - name: "experimental"                            │
│      version: "3.0.0-beta"                           │
│      traffic: 10.0                                   │
└──────────────────────────────────────────────────────┘

Traffic Routing:
┌──────────────┐
│ User Request │
│ user_id=123  │
└──────┬───────┘
       │
       ▼
┌────────────────────────────────┐
│ Routing Strategy Selection     │
│ - Random (default)             │
│ - Hash-based (user_id)         │
│ - Sticky (session_id)          │
└──────┬─────────────────────────┘
       │
       ▼
┌────────────────────────────────┐
│ Calculate Variant              │
│ hash(user_id) % 100            │
│ = 47                           │
└──────┬─────────────────────────┘
       │
       ▼
┌────────────────────────────────┐
│ Traffic Split Mapping          │
│ 0-69   → production (70%)      │
│ 70-89  → candidate_v2 (20%)    │
│ 90-99  → experimental (10%)    │
└──────┬─────────────────────────┘
       │
       │ 47 falls in [0-69]
       ▼
┌────────────────────────────────┐
│ Selected: production           │
│ Load model version 1.0.0       │
└──────┬─────────────────────────┘
       │
       ▼
┌────────────────────────────────┐
│ Track Metrics per Variant      │
│ - variant_requests{v=prod}++   │
│ - variant_latency{v=prod}      │
│ - variant_errors{v=prod}       │
└────────────────────────────────┘

Monitoring Dashboard:
┌─────────────────────────────────────────────────────┐
│              Variant Comparison                     │
├───────────┬────────────┬────────────┬───────────────┤
│ Metric    │ Production │ Candidate  │ Experimental  │
├───────────┼────────────┼────────────┼───────────────┤
│ Requests  │   7,000    │   2,000    │    1,000      │
│ Accuracy  │   87.2%    │   88.5%    │    89.1%      │
│ Latency   │   25ms     │   30ms     │    28ms       │
│ Errors    │   0.1%     │   0.2%     │    0.5%       │
└───────────┴────────────┴────────────┴───────────────┘

Decision Logic:
  candidate_v2.accuracy > production.accuracy + 1%
  AND candidate_v2.latency < production.latency * 1.5
  AND candidate_v2.errors < 1%
  → PROMOTE candidate_v2 to production
```

---

## CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       GitHub Actions CI/CD Pipeline                      │
└─────────────────────────────────────────────────────────────────────────┘

Trigger: Push / Pull Request
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 1: Code Quality                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Black     │  │    isort     │  │   Flake8     │  │
│  │  (Format)    │  │  (Imports)   │  │   (Lint)     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────┬───────────────────────────────────────────┘
              │ ✓ All Pass
              ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 2: Testing                                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  pytest                                          │  │
│  │  - Unit Tests (22 tests)                        │  │
│  │  - Integration Tests                            │  │
│  │  - Coverage Report (>80%)                       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────┬───────────────────────────────────────────┘
              │ ✓ All Pass
              ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 3: Build Validation                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Docker     │  │  Kubernetes  │  │  Terraform   │  │
│  │   Build      │  │  Validation  │  │  Validation  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────┬───────────────────────────────────────────┘
              │ ✓ All Pass
              │
              │ (If branch = main)
              ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 4: Build & Push                                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1. Build Docker Image                           │  │
│  │  2. Tag with git SHA                             │  │
│  │  3. Push to ECR                                  │  │
│  │  4. Scan for vulnerabilities                     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────┬───────────────────────────────────────────┘
              │ ✓ Image Built
              ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 5: Deploy                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1. Update kubeconfig                            │  │
│  │  2. Apply Kubernetes manifests                   │  │
│  │  3. Rolling update (zero downtime)               │  │
│  │  4. Wait for rollout completion                  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────┬───────────────────────────────────────────┘
              │ ✓ Deployed
              ▼
┌─────────────────────────────────────────────────────────┐
│  STAGE 6: Verification                                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  1. Health check endpoint                        │  │
│  │  2. Smoke tests                                  │  │
│  │  3. Monitor error rates                          │  │
│  │  4. Alert on failures                            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────┬───────────────────────────────────────────┘
              │ ✓ Verified
              ▼
         SUCCESS
```

---

## Kubernetes Deployment

```
┌─────────────────────────────────────────────────────────────────────────┐
│              Kubernetes Cluster Architecture (EKS)                       │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  Namespace: mlops-platform                                              │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Ingress (NGINX)                                               │   │
│  │  - TLS Termination                                             │   │
│  │  - Path routing: /api → Service                               │   │
│  └────────────┬───────────────────────────────────────────────────┘   │
│               │                                                         │
│               ▼                                                         │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Service (ClusterIP)                                           │   │
│  │  - Load balancing                                              │   │
│  │  - Service discovery                                           │   │
│  └────────────┬───────────────────────────────────────────────────┘   │
│               │                                                         │
│               ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Deployment: churn-prediction-api                               │  │
│  │                                                                 │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │  │
│  │  │  Pod 1   │  │  Pod 2   │  │  Pod 3   │  │  Pod N   │ ... │  │
│  │  │          │  │          │  │          │  │          │      │  │
│  │  │ FastAPI  │  │ FastAPI  │  │ FastAPI  │  │ FastAPI  │      │  │
│  │  │ Model    │  │ Model    │  │ Model    │  │ Model    │      │  │
│  │  │          │  │          │  │          │  │          │      │  │
│  │  │ CPU: 500m│  │ CPU: 500m│  │ CPU: 500m│  │ CPU: 500m│      │  │
│  │  │ Mem: 1Gi │  │ Mem: 1Gi │  │ Mem: 1Gi │  │ Mem: 1Gi │      │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │  │
│  │                                                                 │  │
│  │  Replicas: 3-10 (auto-scaled by HPA)                          │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  HorizontalPodAutoscaler (HPA)                                  │  │
│  │  - Min Replicas: 3                                              │  │
│  │  - Max Replicas: 10                                             │  │
│  │  - Target CPU: 70%                                              │  │
│  │  - Target Memory: 80%                                           │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  ConfigMap                                                       │  │
│  │  - MODEL_PATH: /models/churn_model.pkl                         │  │
│  │  - LOG_LEVEL: info                                              │  │
│  │  - MLFLOW_URI: http://mlflow:5000                              │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  PersistentVolumeClaim (PVC)                                    │  │
│  │  - Storage: 10Gi                                                │  │
│  │  - Access: ReadWriteOnce                                        │  │
│  │  - Purpose: Model storage                                       │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Secrets                                                         │  │
│  │  - AWS credentials                                              │  │
│  │  - Database passwords                                           │  │
│  │  - API keys                                                     │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

Health Checks:
┌────────────────────────────────────┐
│ Liveness Probe:                    │
│   HTTP GET /health                 │
│   Initial Delay: 30s               │
│   Period: 10s                      │
│   Timeout: 5s                      │
│   Failure Threshold: 3             │
│                                    │
│ Readiness Probe:                   │
│   HTTP GET /health                 │
│   Initial Delay: 10s               │
│   Period: 5s                       │
│   Success Threshold: 1             │
└────────────────────────────────────┘

Rolling Update Strategy:
┌────────────────────────────────────┐
│ Max Surge: 25%                     │
│ Max Unavailable: 25%               │
│                                    │
│ Update Flow:                       │
│ 1. Create new pod                  │
│ 2. Wait for readiness              │
│ 3. Terminate old pod               │
│ 4. Repeat                          │
│                                    │
│ Zero downtime deployment           │
└────────────────────────────────────┘
```

---

## Monitoring and Observability

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Monitoring Stack Architecture                         │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  Data Collection Layer                                                   │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  FastAPI     │  │  Kubernetes  │  │   MLflow     │                 │
│  │  /metrics    │  │  Metrics     │  │  /metrics    │                 │
│  │              │  │              │  │              │                 │
│  │ - Requests   │  │ - CPU        │  │ - Experiments│                 │
│  │ - Latency    │  │ - Memory     │  │ - Models     │                 │
│  │ - Errors     │  │ - Pods       │  │              │                 │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                 │
│         │                 │                 │                          │
│         └─────────────────┼─────────────────┘                          │
│                           │                                            │
└───────────────────────────┼────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Prometheus Server                                                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Scrape Targets (every 15s)                                    │    │
│  │  - FastAPI pods: :8000/metrics                                 │    │
│  │  - Kubernetes: :10250/metrics                                  │    │
│  │  - MLflow: :5000/metrics                                       │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Time Series Database                                          │    │
│  │  - Stores metrics with labels                                  │    │
│  │  - Retention: 15 days                                          │    │
│  │  - Compression                                                 │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Alert Rules                                                    │    │
│  │  - High error rate (>5%)                                       │    │
│  │  - Slow response time (>500ms)                                 │    │
│  │  - Pod crash loop                                              │    │
│  │  - Resource exhaustion                                         │    │
│  └────────────────┬───────────────────────────────────────────────┘    │
└────────────────────┼────────────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Alertmanager                                                            │
│  - Route alerts                                                          │
│  - Deduplication                                                         │
│  - Notification: Slack, Email, PagerDuty                                │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  Grafana Dashboards                                                      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Dashboard: API Overview                                     │      │
│  │  ┌─────────────────┐  ┌─────────────────┐                  │      │
│  │  │ Request Rate    │  │  Error Rate     │                  │      │
│  │  │ 1250 req/s      │  │  0.2%           │                  │      │
│  │  └─────────────────┘  └─────────────────┘                  │      │
│  │  ┌─────────────────┐  ┌─────────────────┐                  │      │
│  │  │ P50 Latency     │  │  P99 Latency    │                  │      │
│  │  │ 25ms            │  │  150ms          │                  │      │
│  │  └─────────────────┘  └─────────────────┘                  │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Dashboard: Model Performance                                │      │
│  │  ┌─────────────────────────────────────────────────────┐    │      │
│  │  │ Prediction Distribution                             │    │      │
│  │  │ Churn=0: 73% | Churn=1: 27%                        │    │      │
│  │  └─────────────────────────────────────────────────────┘    │      │
│  │  ┌─────────────────────────────────────────────────────┐    │      │
│  │  │ Model Confidence Score (Avg)                        │    │      │
│  │  │ 0.82                                                │    │      │
│  │  └─────────────────────────────────────────────────────┘    │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Dashboard: A/B Testing                                      │      │
│  │  ┌────────────────────────────────────────────────────┐     │      │
│  │  │ Variant Comparison Table                           │     │      │
│  │  ├──────────┬───────────┬───────────┬──────────┤     │      │
│  │  │ Variant  │ Traffic   │ Accuracy  │ Latency  │     │      │
│  │  ├──────────┼───────────┼───────────┼──────────┤     │      │
│  │  │ prod     │ 70%       │ 87.2%     │ 25ms     │     │      │
│  │  │ candidate│ 20%       │ 88.5%     │ 30ms     │     │      │
│  │  │ exp      │ 10%       │ 89.1%     │ 28ms     │     │      │
│  │  └──────────┴───────────┴───────────┴──────────┘     │      │
│  └──────────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘

Key Metrics:
┌────────────────────────────────────────────────────┐
│ Application Metrics:                               │
│ - churn_predictions_total                          │
│ - churn_prediction_duration_seconds                │
│ - churn_model_confidence                           │
│ - variant_requests{variant="production"}           │
│ - variant_errors{variant="candidate"}              │
│                                                    │
│ Infrastructure Metrics:                            │
│ - container_cpu_usage_seconds_total                │
│ - container_memory_working_set_bytes               │
│ - kube_pod_status_phase                            │
│ - kube_deployment_status_replicas                  │
└────────────────────────────────────────────────────┘
```

---

## AWS Cloud Infrastructure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AWS Infrastructure (Terraform)                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  AWS Account: Production                                                │
│  Region: us-east-1                                                      │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  VPC: 10.0.0.0/16                                                │ │
│  │                                                                  │ │
│  │  ┌────────────────────────┐  ┌────────────────────────┐        │ │
│  │  │  Public Subnets        │  │  Private Subnets       │        │ │
│  │  │  (10.0.1.0/24)         │  │  (10.0.11.0/24)        │        │ │
│  │  │  (10.0.2.0/24)         │  │  (10.0.12.0/24)        │        │ │
│  │  │                        │  │                        │        │ │
│  │  │  ┌──────────────────┐ │  │  ┌──────────────────┐ │        │ │
│  │  │  │ NAT Gateway      │ │  │  │  EKS Worker     │ │        │ │
│  │  │  │                  │ │  │  │  Nodes          │ │        │ │
│  │  │  │ Elastic IP       │ │  │  │  (t3.medium)    │ │        │ │
│  │  │  └──────────────────┘ │  │  │  2-6 nodes      │ │        │ │
│  │  │                        │  │  │                 │ │        │ │
│  │  │  ┌──────────────────┐ │  │  └──────────────────┘ │        │ │
│  │  │  │ ALB              │ │  │                        │        │ │
│  │  │  │ (Load Balancer)  │ │  │  ┌──────────────────┐ │        │ │
│  │  │  └──────────────────┘ │  │  │ Application Pods │ │        │ │
│  │  │                        │  │  │                 │ │        │ │
│  │  └────────┬───────────────┘  │  └──────────────────┘ │        │ │
│  │           │                  │                        │        │ │
│  │           │  Internet Gateway│                        │        │ │
│  │           └──────────────────┴────────────────────────┘        │ │
│  │                                                                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  EKS Cluster: mlops-platform-prod                                │ │
│  │  - Version: 1.28                                                 │ │
│  │  - Node Group: 2-6 t3.medium instances                          │ │
│  │  - OIDC Provider for IRSA                                       │ │
│  │  - Cluster Autoscaler enabled                                   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  S3 Buckets                                                      │ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐│ │
│  │  │ mlops-models     │  │ mlops-data       │  │ mlops-artifacts││ │
│  │  │ - Versioning: On │  │ - Versioning: On │  │ - Logs         ││ │
│  │  │ - Encryption:AES │  │ - Encryption:AES │  │ - Backups      ││ │
│  │  │ - Lifecycle: 90d │  │ - Lifecycle: 30d │  │ - Experiments  ││ │
│  │  └──────────────────┘  └──────────────────┘  └────────────────┘│ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  ECR (Container Registry)                                        │ │
│  │  - Repository: mlops-platform-api                               │ │
│  │  - Image Scanning: On                                           │ │
│  │  - Lifecycle: Keep last 10 tagged, expire untagged after 7d    │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  IAM Roles & Policies                                            │ │
│  │  - EKS Cluster Role                                              │ │
│  │  - EKS Node Group Role                                           │ │
│  │  - Service Account Role (IRSA for S3 access)                    │ │
│  │  - CI/CD Role (GitHub Actions)                                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  RDS PostgreSQL (Optional)                                       │ │
│  │  - Instance: db.t3.micro                                         │ │
│  │  - Storage: 20GB                                                 │ │
│  │  - Multi-AZ: No (for cost)                                       │ │
│  │  - Backup: 7 days retention                                     │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  CloudWatch                                                       │ │
│  │  - Log Groups: /aws/eks/mlops-platform                          │ │
│  │  - Alarms: CPU, Memory, Disk                                    │ │
│  │  - Retention: 30 days                                            │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

Terraform Modules:
┌────────────────────────────────────────┐
│ modules/                               │
│ ├── vpc/                               │
│ │   ├── main.tf                        │
│ │   ├── variables.tf                   │
│ │   └── outputs.tf                     │
│ ├── eks/                               │
│ │   ├── main.tf                        │
│ │   ├── variables.tf                   │
│ │   └── outputs.tf                     │
│ ├── s3/                                │
│ │   ├── main.tf                        │
│ │   └── outputs.tf                     │
│ ├── iam/                               │
│ │   └── main.tf                        │
│ └── ecr/                               │
│     └── main.tf                        │
└────────────────────────────────────────┘

Cost Estimate:
┌────────────────────────────────────────┐
│ EKS Control Plane:    $73/month        │
│ EC2 Nodes (3x t3.med): $100/month      │
│ NAT Gateway:          $32/month        │
│ ALB:                  $20/month        │
│ S3 Storage (100GB):   $2/month         │
│ Data Transfer:        $10/month        │
│ ─────────────────────────────────────  │
│ Total:                ~$240/month      │
└────────────────────────────────────────┘
```

---

## Request Flow Diagram (Complete Journey)

```
┌─────────────────────────────────────────────────────────────────────────┐
│               Complete Request Flow (End-to-End)                         │
└─────────────────────────────────────────────────────────────────────────┘

1. CLIENT REQUEST
   │
   │ POST /api/v1/predict
   │ {
   │   "tenure_months": 24,
   │   "monthly_charges": 75.5,
   │   "user_id": "user_123"
   │ }
   │
   ▼
2. AWS ALB (Load Balancer)
   │ - TLS termination
   │ - Health check
   │ - Route to healthy target
   │
   ▼
3. Kubernetes Ingress
   │ - Path matching
   │ - Rate limiting
   │
   ▼
4. Kubernetes Service
   │ - Load balance across pods
   │ - Service discovery
   │
   ▼
5. FastAPI Pod (Selected)
   │
   ├─▶ Request Validation (Pydantic)
   │   └─▶ Pass
   │
   ├─▶ A/B Test Manager
   │   │ - Hash(user_123) = 47
   │   │ - 0-69 → production
   │   └─▶ Select: production v1.0.0
   │
   ├─▶ Feature Store Query (Optional)
   │   │ GET /api/v1/predict/features
   │   │
   │   ├─▶ Feast Online Store (Redis)
   │   │   └─▶ Retrieve: tenure, charges, etc.
   │   │
   │   └─▶ Merge with request data
   │
   ├─▶ Model Inference
   │   │ - Load model from memory
   │   │ - Preprocess features
   │   │ - model.predict_proba(X)
   │   └─▶ Result: [0.27, 0.73]
   │
   ├─▶ Post-processing
   │   │ - Extract prediction: 1
   │   │ - Extract probability: 0.73
   │   └─▶ Format response
   │
   ├─▶ Metrics Collection
   │   │ - prediction_counter.inc()
   │   │ - prediction_latency.observe(0.025)
   │   │ - variant_requests{v="prod"}.inc()
   │   └─▶ Exported to Prometheus
   │
   └─▶ Return Response
       │
       ▼
6. Response to Client
   {
     "prediction": 1,
     "probability": 0.73,
     "model_variant": "production",
     "model_version": "1.0.0"
   }
   │
   ▼
7. Monitoring (Async)
   │
   ├─▶ Prometheus scrapes /metrics
   │   └─▶ Stores in TSDB
   │
   ├─▶ Grafana visualizes
   │   └─▶ Updates dashboards
   │
   └─▶ Alertmanager checks rules
       └─▶ No alerts triggered

Total Time: ~30ms
```

---

## Summary

This document provides comprehensive visual diagrams of the complete MLOps platform architecture, covering:

- **High-level system architecture**: Complete component overview
- **Data pipeline**: From ingestion to feature store
- **Feature store**: Feast architecture with online/offline stores
- **Model training**: MLflow integration and experiment tracking
- **Prediction service**: FastAPI with A/B testing
- **A/B testing**: Traffic routing and variant selection
- **CI/CD pipeline**: Automated testing and deployment
- **Kubernetes**: Container orchestration and scaling
- **Monitoring**: Prometheus and Grafana stack
- **AWS infrastructure**: Cloud resources and networking

Each diagram can be used independently or referenced together to understand the complete system design and data flows.
