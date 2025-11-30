locals {
  name = "${var.project_name}-${var.environment}"
}

# S3 Bucket for ML Models
resource "aws_s3_bucket" "models" {
  bucket = "${local.name}-models"

  tags = merge(
    var.tags,
    {
      Name    = "${local.name}-models"
      Purpose = "ML model storage"
    }
  )
}

resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "models" {
  bucket = aws_s3_bucket.models.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "models" {
  bucket = aws_s3_bucket.models.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "models" {
  bucket = aws_s3_bucket.models.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = var.lifecycle_days
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = var.lifecycle_days * 2
      storage_class = "GLACIER"
    }
  }
}

# S3 Bucket for Training Data
resource "aws_s3_bucket" "data" {
  bucket = "${local.name}-data"

  tags = merge(
    var.tags,
    {
      Name    = "${local.name}-data"
      Purpose = "Training data storage"
    }
  )
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket for Artifacts and Logs
resource "aws_s3_bucket" "artifacts" {
  bucket = "${local.name}-artifacts"

  tags = merge(
    var.tags,
    {
      Name    = "${local.name}-artifacts"
      Purpose = "Artifacts and logs storage"
    }
  )
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    expiration {
      days = var.lifecycle_days * 3
    }
  }
}
