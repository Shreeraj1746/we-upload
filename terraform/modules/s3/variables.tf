variable "project_name" {
  description = "Name of the project for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
}

variable "enable_lifecycle_rules" {
  description = "Whether to enable lifecycle rules for cost optimization"
  type        = bool
  default     = true
}

variable "expiration_days" {
  description = "Number of days before objects expire"
  type        = number
  default     = 365
}
