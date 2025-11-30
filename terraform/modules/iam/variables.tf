variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "eks_cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "eks_oidc_provider_arn" {
  description = "EKS OIDC provider ARN"
  type        = string
}

variable "s3_models_bucket_arn" {
  description = "S3 models bucket ARN"
  type        = string
}

variable "s3_data_bucket_arn" {
  description = "S3 data bucket ARN"
  type        = string
}

variable "s3_artifacts_bucket_arn" {
  description = "S3 artifacts bucket ARN"
  type        = string
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
}
