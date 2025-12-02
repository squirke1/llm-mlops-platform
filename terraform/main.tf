module "vpc" {
  source = "./modules/vpc"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  enable_nat_gateway = var.enable_nat_gateway
  single_nat_gateway = var.single_nat_gateway
  tags               = var.tags
}

module "eks" {
  source = "./modules/eks"

  project_name        = var.project_name
  environment         = var.environment
  cluster_version     = var.eks_cluster_version
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  node_instance_types = var.eks_node_instance_types
  node_desired_size   = var.eks_node_desired_size
  node_min_size       = var.eks_node_min_size
  node_max_size       = var.eks_node_max_size
  tags                = var.tags
}

module "s3" {
  source = "./modules/s3"

  project_name      = var.project_name
  environment       = var.environment
  enable_versioning = var.enable_s3_versioning
  lifecycle_days    = var.s3_lifecycle_days
  tags              = var.tags
}

module "iam" {
  source = "./modules/iam"

  project_name            = var.project_name
  environment             = var.environment
  eks_cluster_name        = module.eks.cluster_name
  eks_oidc_provider_arn   = module.eks.oidc_provider_arn
  s3_models_bucket_arn    = module.s3.models_bucket_arn
  s3_data_bucket_arn      = module.s3.data_bucket_arn
  s3_artifacts_bucket_arn = module.s3.artifacts_bucket_arn
  tags                    = var.tags
}

module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
  environment  = var.environment
  tags         = var.tags
}
