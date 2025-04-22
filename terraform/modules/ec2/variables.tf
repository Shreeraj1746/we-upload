variable "project_name" {
  description = "Name of the project for resource naming"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC where the EC2 instance will be deployed"
  type        = string
}

variable "public_subnet_id" {
  description = "ID of the public subnet where the EC2 instance will be deployed"
  type        = string
}

variable "ec2_role_name" {
  description = "Name of the IAM role for EC2 instance"
  type        = string
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
  default     = "ami-0261755bbcb8c4a84" # Ubuntu 20.04 LTS in ap-south-1
}

variable "ssh_key_name" {
  description = "Name of the SSH key pair for EC2 instance"
  type        = string
}
