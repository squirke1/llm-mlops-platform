aws_region         = "us-east-1"
environment        = "prod"
project_name       = "mlops-platform"
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

eks_cluster_version      = "1.28"
eks_node_instance_types  = ["t3.medium"]
eks_node_desired_size    = 3
eks_node_min_size        = 2
eks_node_max_size        = 6

enable_nat_gateway   = true
single_nat_gateway   = true
enable_s3_versioning = true
s3_lifecycle_days    = 90

tags = {
  Owner = "MLOps Team"
  CostCenter = "Engineering"
}
