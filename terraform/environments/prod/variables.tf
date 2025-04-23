variable "aws_region" {
  description = "AWS region where resources will be deployed"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "we-upload"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "create_nat_gateway" {
  description = "Whether to create a NAT Gateway (adds cost)"
  type        = bool
  default     = false
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for the public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for the private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
}

variable "enable_lifecycle_rules" {
  description = "Enable S3 bucket lifecycle rules"
  type        = bool
  default     = true
}

variable "expiration_days" {
  description = "Number of days after which objects in the S3 bucket expire"
  type        = number
  default     = 90 # Longer retention for production
}

variable "ssh_public_key_path" {
  description = "Path to the SSH public key file"
  type        = string
}

variable "db_password" {
  description = "Password for the database"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Name of the database"
  type        = string
}

# EC2 production variables
variable "ec2_instance_type" {
  description = "EC2 instance type for the application server"
  type        = string
  default     = "t2.micro" # Still using free tier, but could be upgraded for production
}

# RDS production variables
variable "rds_instance_class" {
  description = "RDS instance class for the database"
  type        = string
  default     = "db.t3.micro" # Still using free tier, but could be upgraded for production
}

variable "rds_multi_az" {
  description = "Whether the RDS instance should be multi-AZ"
  type        = bool
  default     = false # Set to true for production high availability (adds cost)
}

variable "rds_backup_retention_days" {
  description = "Number of days to retain RDS backups"
  type        = number
  default     = 7 # One week of backups for production
}

variable "rds_allocated_storage" {
  description = "Allocated storage for the RDS instance in GB"
  type        = number
  default     = 20 # Minimum for production
}
