variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "enable_versioning" {
  description = "Enable S3 versioning"
  type        = bool
}

variable "lifecycle_days" {
  description = "Days before transitioning to cheaper storage"
  type        = number
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
}
