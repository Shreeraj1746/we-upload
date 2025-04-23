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

  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr

  # In production we might want NAT Gateway for private subnet internet access
  # Only enable if you're willing to pay for it
  create_nat_gateway = var.create_nat_gateway

  # Use availability zones for the region
  availability_zones = [
    "${var.aws_region}a",
    "${var.aws_region}b",
    "${var.aws_region}c" # Add a third AZ for production reliability
  ]

  # Use subnet CIDRs
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

# S3 Module with production settings
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

# EC2 Module for production
module "ec2" {
  source = "../../modules/ec2"

  project_name     = var.project_name
  vpc_id           = module.vpc.vpc_id
  public_subnet_id = module.vpc.public_subnet_ids[0]
  ec2_role_name    = module.iam.ec2_role_name
  ssh_key_name     = aws_key_pair.ssh_key.key_name

  # For additional production-specific configurations,
  # extend the EC2 module to accept these parameters
}

# RDS Module for production
module "rds" {
  source = "../../modules/rds"

  project_name          = var.project_name
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  ec2_security_group_id = module.ec2.ec2_security_group_id

  # Use AWS Secrets Manager instead of hardcoded passwords in production
  db_password = var.db_password

  # For additional production-specific configurations,
  # extend the RDS module to accept these parameters
}
