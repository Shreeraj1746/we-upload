terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration will be added later
  # backend "s3" {}
}

locals {
  project_name = "we-upload"
  region       = "ap-south-1"
  environment  = "dev"
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  project_name       = local.project_name
  environment        = local.environment
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["${local.region}a", "${local.region}b"]
  create_nat_gateway = false # Set to true if needed, but not free tier eligible
}

# S3 Module
module "s3" {
  source = "./modules/s3"

  project_name = local.project_name
  environment  = local.environment
}

# IAM Module
module "iam" {
  source = "./modules/iam"

  project_name  = local.project_name
  environment   = local.environment
  s3_bucket_arn = module.s3.s3_bucket_arn
}

# Create SSH key pair
resource "aws_key_pair" "ssh_key" {
  key_name   = "${local.project_name}-ssh-key"
  public_key = file(var.ssh_public_key_path)
}

# EC2 Module
module "ec2" {
  source = "./modules/ec2"

  project_name     = local.project_name
  vpc_id           = module.vpc.vpc_id
  public_subnet_id = module.vpc.public_subnet_ids[0]
  ec2_role_name    = module.iam.ec2_role_name
  ssh_key_name     = aws_key_pair.ssh_key.key_name
}

# RDS Module
module "rds" {
  source = "./modules/rds"

  project_name          = local.project_name
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  ec2_security_group_id = module.ec2.ec2_security_group_id
  db_password           = var.db_password
}
