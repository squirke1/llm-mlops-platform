locals {
  name              = "${var.project_name}-${var.environment}"
  oidc_provider_url = replace(var.eks_oidc_provider_arn, "/^(.*provider/)/", "")
}

# IAM Role for EKS Service Account (IRSA)
resource "aws_iam_role" "eks_service_account" {
  name = "${local.name}-eks-sa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRoleWithWebIdentity"
      Effect = "Allow"
      Principal = {
        Federated = var.eks_oidc_provider_arn
      }
      Condition = {
        StringEquals = {
          "${local.oidc_provider_url}:sub" = "system:serviceaccount:mlops-platform:churn-prediction-api"
          "${local.oidc_provider_url}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = var.tags
}

# IAM Policy for S3 Access
resource "aws_iam_policy" "s3_access" {
  name        = "${local.name}-s3-access"
  description = "Policy for accessing S3 buckets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_models_bucket_arn,
          "${var.s3_models_bucket_arn}/*",
          var.s3_data_bucket_arn,
          "${var.s3_data_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_artifacts_bucket_arn,
          "${var.s3_artifacts_bucket_arn}/*"
        ]
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "eks_sa_s3_access" {
  policy_arn = aws_iam_policy.s3_access.arn
  role       = aws_iam_role.eks_service_account.name
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_policy" "cloudwatch_logs" {
  name        = "${local.name}-cloudwatch-logs"
  description = "Policy for writing CloudWatch logs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "arn:aws:logs:*:*:*"
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "eks_sa_cloudwatch_logs" {
  policy_arn = aws_iam_policy.cloudwatch_logs.arn
  role       = aws_iam_role.eks_service_account.name
}
