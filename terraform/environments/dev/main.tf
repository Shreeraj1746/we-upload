terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # configure for remote state
  backend "s3" {
    bucket         = "we-upload-terraform-state"
    key            = "environments/dev/terraform.tfstate" # Replace 'dev' with your environment name
    region         = "ap-south-1"
    dynamodb_table = "we-upload-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  create_nat_gateway = false # Explicitly set to false to avoid costs

  # Use availability zones for the region
  availability_zones = [
    "${var.aws_region}a",
    "${var.aws_region}b"
  ]

  # Use subnet CIDRs
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

# S3 Module
module "s3" {
  source = "../../modules/s3"

  project_name           = var.project_name
  environment            = var.environment
  enable_lifecycle_rules = var.enable_lifecycle_rules
  expiration_days        = var.expiration_days
}

# IAM Module
module "iam" {
  source = "../../modules/iam"

  project_name  = var.project_name
  environment   = var.environment
  s3_bucket_arn = module.s3.s3_bucket_arn
}

# Create SSH key pair
resource "aws_key_pair" "ssh_key" {
  key_name   = "${var.project_name}-${var.environment}-ssh-key"
  public_key = file(var.ssh_public_key_path)
}

# EC2 Module
module "ec2" {
  source = "../../modules/ec2"

  project_name     = var.project_name
  vpc_id           = module.vpc.vpc_id
  public_subnet_id = module.vpc.public_subnet_ids[0]
  ec2_role_name    = module.iam.ec2_role_name
  ssh_key_name     = aws_key_pair.ssh_key.key_name

  # Additional variables for user data
  aws_region     = var.aws_region
  s3_bucket_name = module.s3.s3_bucket_name
  db_host        = module.rds.db_endpoint
  db_username    = module.rds.db_username
  db_password    = var.db_password
  db_name        = module.rds.db_name
}

# RDS Module
module "rds" {
  source = "../../modules/rds"

  project_name          = var.project_name
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  ec2_security_group_id = module.ec2.ec2_security_group_id
  db_password           = var.db_password
}
