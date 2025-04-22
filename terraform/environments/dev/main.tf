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

  # Use default availability zones for the region
  availability_zones = [
    "${var.aws_region}a",
    "${var.aws_region}b"
  ]

  # Use default subnet CIDRs
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
  s3_bucket_arn = module.s3.bucket_arn
}

module "weupload" {
  source = "../../"

  # Variables specific to dev environment
  aws_region          = "ap-south-1"
  ssh_public_key_path = "~/.ssh/id_rsa.pub"
  db_password         = "DevPassword123!" # Use AWS Secrets Manager in production
}
