# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the ML Churn Prediction API.

## 📦 What's Included

- **namespace.yaml** - Isolated namespace for MLOps resources
- **configmap.yaml** - Non-sensitive configuration (model path, log level)
- **pvc.yaml** - PersistentVolumeClaim for model storage
- **deployment.yaml** - 3 replicas with health checks and resource limits
- **service.yaml** - ClusterIP service for internal pod communication
- **ingress.yaml** - NGINX ingress for external access
- **hpa.yaml** - Horizontal Pod Autoscaler (scales 3-10 pods based on CPU/memory)
- **kustomization.yaml** - Kustomize configuration for managing manifests

## 🚀 Local Testing with Minikube

### Prerequisites
```bash
# Install Minikube
brew install minikube

# Install kubectl
brew install kubectl
```

### Start Minikube
```bash
minikube start --driver=docker
minikube addons enable ingress
```

### Build Docker Image in Minikube
```bash
# Point Docker to Minikube's Docker daemon
eval $(minikube docker-env)

# Build image (will be available in Minikube)
docker build -t churn-prediction-api:latest .
```

### Deploy to Minikube
```bash
# Apply all manifests
kubectl apply -k k8s/

# Check deployment status
kubectl get all -n mlops-platform
kubectl get pods -n mlops-platform
kubectl get svc -n mlops-platform
kubectl get ingress -n mlops-platform

# View logs
kubectl logs -n mlops-platform -l app=churn-prediction-api --tail=50

# Watch HPA scale
kubectl get hpa -n mlops-platform --watch
```

### Access the API
```bash
# Get Minikube IP
minikube ip

# Add to /etc/hosts
echo "$(minikube ip) churn-api.local" | sudo tee -a /etc/hosts

# Test API
curl http://churn-api.local/health
curl -X POST http://churn-api.local/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "tenure_months": 24,
    "monthly_charges": 75.5,
    "total_charges": 1800.0,
    "contract_type": "month-to-month",
    "num_support_tickets": 2
  }'
```

### Load Model into Cluster
```bash
# Copy model to Minikube node
kubectl create configmap model-files --from-file=models/churn_model.pkl -n mlops-platform

# Or use PVC (requires model to be in persistent storage)
```

### Clean Up
```bash
# Delete all resources
kubectl delete -k k8s/

# Stop Minikube
minikube stop

# Delete cluster
minikube delete
```

## 🏗️ Production Deployment (AWS EKS)

### Prerequisites
- AWS CLI configured
- eksctl installed
- kubectl configured for EKS cluster

### Deploy to EKS
```bash
# Update image to use ECR
# Edit deployment.yaml: image: <account-id>.dkr.ecr.us-east-1.amazonaws.com/churn-prediction-api:latest

# Apply manifests
kubectl apply -k k8s/

# Get Load Balancer URL
kubectl get ingress -n mlops-platform
```

## 🔍 Key Kubernetes Concepts

### Namespace
Isolates resources from other applications in the cluster. Like a virtual cluster within a cluster.

### ConfigMap
Stores non-sensitive configuration as key-value pairs. Injected as environment variables into pods.

### PersistentVolumeClaim (PVC)
Requests storage from the cluster. In production, backed by cloud storage (EBS, EFS).

### Deployment
Manages pod replicas, rolling updates, and rollbacks. Ensures desired number of pods are always running.

### Service
Stable network endpoint for pods. ClusterIP type = internal only, LoadBalancer = external.

### Ingress
Routes external HTTP/S traffic to services. Requires ingress controller (NGINX, ALB).

### HorizontalPodAutoscaler (HPA)
Automatically scales pods based on CPU/memory metrics. Scales from 3 to 10 replicas when CPU > 70%.

### Resource Requests & Limits
- **Requests**: Minimum guaranteed resources (used for scheduling)
- **Limits**: Maximum resources pod can consume (prevents resource hogging)

### Health Checks
- **Liveness Probe**: Restarts pod if unhealthy
- **Readiness Probe**: Removes pod from load balancer if not ready

## 📊 Monitoring & Debugging

```bash
# Describe deployment
kubectl describe deployment churn-prediction-api -n mlops-platform

# Get pod details
kubectl describe pod <pod-name> -n mlops-platform

# Check events
kubectl get events -n mlops-platform --sort-by='.lastTimestamp'

# Port forward to local
kubectl port-forward -n mlops-platform svc/churn-prediction-api 8000:80

# Execute command in pod
kubectl exec -it -n mlops-platform <pod-name> -- /bin/bash
```

## 🎯 Interview Talking Points

1. **Scalability**: HPA automatically scales from 3-10 pods based on load
2. **High Availability**: 3 replicas across nodes with anti-affinity
3. **Resource Management**: CPU/memory requests prevent resource contention
4. **Health Monitoring**: Liveness/readiness probes ensure pod reliability
5. **Configuration Management**: ConfigMaps decouple config from code
6. **Storage**: PVC abstracts storage from infrastructure
7. **Service Discovery**: Kubernetes DNS for service-to-service communication
8. **Rolling Updates**: Zero-downtime deployments with rolling update strategy
9. **Infrastructure as Code**: Declarative YAML manifests in version control
10. **Environment Portability**: Same manifests work on Minikube, EKS, GKE, AKS
