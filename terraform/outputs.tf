output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = module.vpc.vpc_cidr
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
  sensitive   = true
}

output "eks_cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = module.eks.cluster_security_group_id
}

output "eks_node_group_role_arn" {
  description = "EKS node group IAM role ARN"
  value       = module.eks.node_group_role_arn
}

output "s3_models_bucket_name" {
  description = "S3 bucket for ML models"
  value       = module.s3.models_bucket_name
}

output "s3_data_bucket_name" {
  description = "S3 bucket for training data"
  value       = module.s3.data_bucket_name
}

output "s3_artifacts_bucket_name" {
  description = "S3 bucket for artifacts and logs"
  value       = module.s3.artifacts_bucket_name
}

output "ecr_repository_url" {
  description = "ECR repository URL for Docker images"
  value       = module.ecr.repository_url
}

output "ecr_repository_arn" {
  description = "ECR repository ARN"
  value       = module.ecr.repository_arn
}

output "eks_service_account_role_arn" {
  description = "IAM role ARN for EKS service account"
  value       = module.iam.eks_service_account_role_arn
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}
