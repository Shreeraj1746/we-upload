variable "aws_region" {
  description = "AWS region to deploy resources to"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "we-upload"
}

variable "ssh_public_key_path" {
  description = "Path to the SSH public key file to use for EC2 instance"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "db_password" {
  description = "Password for the RDS database"
  type        = string
  sensitive   = true
}
