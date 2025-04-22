variable "project_name" {
  description = "Name of the project for resource naming"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC where the RDS instance will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs where the RDS instance will be deployed"
  type        = list(string)
}

variable "ec2_security_group_id" {
  description = "ID of the EC2 security group that needs access to the RDS instance"
  type        = string
}

variable "db_name" {
  description = "Name of the database to create"
  type        = string
  default     = "weupload"
}

variable "db_username" {
  description = "Username for the database"
  type        = string
  default     = "weuploadadmin"
}

variable "db_password" {
  description = "Password for the database"
  type        = string
  sensitive   = true
}
