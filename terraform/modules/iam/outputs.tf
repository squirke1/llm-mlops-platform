output "eks_service_account_role_arn" {
  description = "IAM role ARN for EKS service account"
  value       = aws_iam_role.eks_service_account.arn
}

output "eks_service_account_role_name" {
  description = "IAM role name for EKS service account"
  value       = aws_iam_role.eks_service_account.name
}
