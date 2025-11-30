output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_ca_certificate" {
  description = "EKS cluster CA certificate"
  value       = aws_eks_cluster.main.certificate_authority[0].data
}

output "cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

output "node_group_role_arn" {
  description = "EKS node group IAM role ARN"
  value       = aws_iam_role.node_group.arn
}

output "oidc_provider_arn" {
  description = "OIDC provider ARN for service accounts"
  value       = aws_iam_openid_connect_provider.eks.arn
}
