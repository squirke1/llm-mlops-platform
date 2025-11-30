output "models_bucket_name" {
  description = "S3 bucket name for ML models"
  value       = aws_s3_bucket.models.bucket
}

output "models_bucket_arn" {
  description = "S3 bucket ARN for ML models"
  value       = aws_s3_bucket.models.arn
}

output "data_bucket_name" {
  description = "S3 bucket name for training data"
  value       = aws_s3_bucket.data.bucket
}

output "data_bucket_arn" {
  description = "S3 bucket ARN for training data"
  value       = aws_s3_bucket.data.arn
}

output "artifacts_bucket_name" {
  description = "S3 bucket name for artifacts"
  value       = aws_s3_bucket.artifacts.bucket
}

output "artifacts_bucket_arn" {
  description = "S3 bucket ARN for artifacts"
  value       = aws_s3_bucket.artifacts.arn
}
