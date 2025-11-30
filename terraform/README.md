# Terraform AWS Infrastructure

Infrastructure as Code (IaC) for the MLOps Platform using Terraform.

## 🏗️ Architecture Overview

This Terraform configuration deploys a complete AWS infrastructure for the ML Churn Prediction API:

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Account                           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              VPC (10.0.0.0/16)                     │    │
│  │                                                    │    │
│  │  ┌─────────────────┐  ┌──────────────────┐       │    │
│  │  │ Public Subnets  │  │ Private Subnets  │       │    │
│  │  │  - NAT Gateway  │  │  - EKS Nodes     │       │    │
│  │  │  - IGW          │  │  - App Pods      │       │    │
│  │  └─────────────────┘  └──────────────────┘       │    │
│  │                                                    │    │
│  │  ┌──────────────────────────────────────────┐    │    │
│  │  │         EKS Cluster (1.28)               │    │    │
│  │  │  - 2-6 t3.medium nodes                   │    │    │
│  │  │  - Auto-scaling enabled                  │    │    │
│  │  │  - IRSA for S3 access                    │    │    │
│  │  └──────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │                 S3 Buckets                         │    │
│  │  - mlops-platform-prod-models                      │    │
│  │  - mlops-platform-prod-data                        │    │
│  │  - mlops-platform-prod-artifacts                   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │          ECR (Container Registry)                  │    │
│  │  - mlops-platform-prod-api                         │    │
│  │  - Image scanning enabled                          │    │
│  │  - Lifecycle policies                              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Resources Created

### Networking (VPC Module)
- **VPC**: 10.0.0.0/16 with DNS enabled
- **Public Subnets**: 2 subnets across AZs for load balancers
- **Private Subnets**: 2 subnets for EKS nodes
- **Internet Gateway**: For public subnet internet access
- **NAT Gateway**: For private subnet outbound access (single NAT for cost savings)
- **Route Tables**: Separate for public/private subnets

### Compute (EKS Module)
- **EKS Cluster**: Kubernetes 1.28
- **Node Group**: 2-6 t3.medium instances with auto-scaling
- **OIDC Provider**: For IAM Roles for Service Accounts (IRSA)
- **Security Groups**: Cluster and node security
- **IAM Roles**: Cluster and node group roles with required policies

### Storage (S3 Module)
- **Models Bucket**: Versioned storage for ML models
- **Data Bucket**: Training/inference data storage
- **Artifacts Bucket**: Logs, metrics, experiment artifacts
- **Encryption**: AES256 server-side encryption
- **Lifecycle Policies**: Automatic transition to IA/Glacier
- **Public Access Block**: All buckets private by default

### Identity (IAM Module)
- **Service Account Role**: IRSA role for pods to access S3
- **S3 Access Policy**: Read/write permissions for buckets
- **CloudWatch Logs Policy**: Log writing permissions

### Container Registry (ECR Module)
- **Repository**: For Docker images
- **Image Scanning**: Automatic vulnerability scanning
- **Lifecycle Policy**: Keep last 10 tagged images, expire untagged after 7 days

## 🚀 Prerequisites

### Install Tools
```bash
# Install Terraform
brew install terraform

# Install AWS CLI
brew install awscli

# Install kubectl
brew install kubectl
```

### Configure AWS Credentials
```bash
# Configure AWS CLI
aws configure

# Verify credentials
aws sts get-caller-identity
```

### Create S3 Backend (First Time Only)
```bash
# Create S3 bucket for Terraform state
aws s3api create-bucket \
  --bucket mlops-platform-terraform-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket mlops-platform-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name mlops-platform-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

## 📝 Configuration

### Variables
Edit `terraform.tfvars` to customize:
- **aws_region**: AWS region (default: us-east-1)
- **environment**: Environment name (prod, staging, dev)
- **vpc_cidr**: VPC CIDR block
- **eks_cluster_version**: Kubernetes version
- **eks_node_instance_types**: EC2 instance types
- **eks_node_desired_size**: Number of nodes (default: 3)
- **single_nat_gateway**: Use 1 NAT for cost savings (default: true)

## 🛠️ Deployment

### Initialize Terraform
```bash
cd terraform/
terraform init
```

### Plan Infrastructure
```bash
# Review changes
terraform plan

# Save plan to file
terraform plan -out=tfplan
```

### Apply Infrastructure
```bash
# Apply saved plan
terraform apply tfplan

# Or apply directly (with confirmation)
terraform apply
```

### Configure kubectl
```bash
# Update kubeconfig
aws eks update-kubeconfig \
  --region us-east-1 \
  --name mlops-platform-prod-cluster

# Verify connection
kubectl get nodes
kubectl get namespaces
```

## 🔄 Deploy Application to EKS

### Build and Push Docker Image
```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t churn-prediction-api:latest .

# Tag for ECR
ECR_URL=$(terraform output -raw ecr_repository_url)
docker tag churn-prediction-api:latest $ECR_URL:latest

# Push to ECR
docker push $ECR_URL:latest
```

### Update Kubernetes Manifests
```bash
# Update deployment.yaml with ECR image URL
ECR_URL=$(terraform output -raw ecr_repository_url)
sed -i '' "s|image: churn-prediction-api:latest|image: $ECR_URL:latest|" ../k8s/deployment.yaml
```

### Upload Model to S3
```bash
# Copy model to S3
S3_BUCKET=$(terraform output -raw s3_models_bucket_name)
aws s3 cp ../models/churn_model.pkl s3://$S3_BUCKET/churn_model.pkl
```

### Deploy to EKS
```bash
# Apply Kubernetes manifests
kubectl apply -k ../k8s/

# Check deployment
kubectl get all -n mlops-platform
kubectl logs -n mlops-platform -l app=churn-prediction-api --tail=50
```

## 📊 Monitoring & Management

### View Resources
```bash
# Get all outputs
terraform output

# Specific output
terraform output eks_cluster_endpoint
terraform output ecr_repository_url
```

### EKS Cluster Info
```bash
# Cluster status
aws eks describe-cluster \
  --name mlops-platform-prod-cluster \
  --region us-east-1

# Node group status
kubectl get nodes -o wide
kubectl top nodes
```

### S3 Buckets
```bash
# List buckets
aws s3 ls | grep mlops-platform

# List bucket contents
aws s3 ls s3://mlops-platform-prod-models/
```

### ECR Images
```bash
# List images
aws ecr list-images \
  --repository-name mlops-platform-prod-api \
  --region us-east-1
```

## 💰 Cost Optimization

### Current Configuration
- **NAT Gateway**: Single NAT ($32/month) vs multi-AZ ($64/month)
- **EKS Cluster**: $72/month
- **EC2 Nodes**: 3 x t3.medium = ~$90/month
- **S3**: Pay per GB stored and accessed
- **Data Transfer**: Minimal within same region

### Estimated Monthly Cost: ~$200

### Reduce Costs
```bash
# Scale down node group
terraform apply -var="eks_node_desired_size=2" -var="eks_node_min_size=1"

# Use smaller instances
terraform apply -var='eks_node_instance_types=["t3.small"]'

# Destroy when not in use
terraform destroy
```

## 🧹 Cleanup

### Destroy Infrastructure
```bash
# Delete Kubernetes resources first
kubectl delete -k ../k8s/

# Destroy AWS resources
terraform destroy

# Confirm when prompted
```

### Manual Cleanup (if needed)
```bash
# Empty S3 buckets
aws s3 rm s3://mlops-platform-prod-models --recursive
aws s3 rm s3://mlops-platform-prod-data --recursive
aws s3 rm s3://mlops-platform-prod-artifacts --recursive

# Delete ECR images
aws ecr batch-delete-image \
  --repository-name mlops-platform-prod-api \
  --image-ids imageTag=latest
```

## 🔐 Security Best Practices

### Implemented
✅ Private subnets for EKS nodes
✅ NAT Gateway for secure outbound access
✅ Security groups restricting traffic
✅ S3 buckets private by default
✅ S3 encryption at rest (AES256)
✅ ECR image scanning enabled
✅ IRSA for fine-grained IAM permissions
✅ EKS cluster logs enabled

### Additional Recommendations
- Enable AWS WAF on ingress
- Set up VPC Flow Logs
- Use AWS Secrets Manager for sensitive data
- Enable GuardDuty for threat detection
- Configure AWS Config for compliance

## 🎯 Key Terraform Concepts

### Modules
Reusable, self-contained infrastructure components. Each module (vpc, eks, s3, iam, ecr) encapsulates related resources.

### State Management
Terraform state stored in S3 with DynamoDB locking prevents concurrent modifications and provides disaster recovery.

### Variables & Outputs
Variables allow customization without code changes. Outputs expose values for use by other tools or modules.

### Resource Dependencies
Terraform automatically handles dependency ordering (e.g., VPC before EKS, IAM roles before node groups).

### Lifecycle Policies
S3 lifecycle rules automatically transition objects to cheaper storage classes, reducing costs.

### IRSA (IAM Roles for Service Accounts)
Kubernetes pods assume IAM roles without storing credentials, following AWS security best practices.

## 🎤 Interview Talking Points

1. **Infrastructure as Code**: Version-controlled, repeatable infrastructure using Terraform
2. **Modular Design**: Reusable modules for vpc, eks, s3, iam, ecr
3. **Cost Optimization**: Single NAT gateway, lifecycle policies, auto-scaling
4. **Security**: Private subnets, encryption, IRSA, no hardcoded credentials
5. **High Availability**: Multi-AZ deployment, auto-scaling node groups
6. **State Management**: Remote state in S3 with DynamoDB locking
7. **Networking**: VPC with public/private subnets, NAT for private subnet internet access
8. **Container Orchestration**: EKS for managed Kubernetes with ECR for images
9. **Storage Strategy**: Separate S3 buckets for models, data, artifacts with versioning
10. **Observability**: EKS cluster logs, CloudWatch integration ready

## 📚 Next Steps

After deploying infrastructure:
1. **Phase 7**: Set up CI/CD pipeline with GitHub Actions
2. **Phase 8**: Add monitoring with Prometheus & Grafana
3. **Phase 9**: Implement MLflow for model versioning
4. **Phase 10**: Production hardening (WAF, GuardDuty, backups)
