locals {
  env         = "dev"
  aws_region  = "us-east-1"

  # VPC configuration
  vpc_cidr_block            = "10.0.0.0/16"
  public_subnet_cidr_blocks = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidr_blocks = ["10.0.11.0/24", "10.0.12.0/24"]
  enable_nat_gateway        = false  # No NAT Gateway in dev to save costs

  # EC2 configuration
  instance_type             = "t2.micro"  # Free tier eligible

  # Database configuration
  db_instance_class         = "db.t3.micro"  # Free tier eligible
  db_allocated_storage      = 20
  db_name                   = "we_upload"
  db_username               = "postgres"  # Override with environment variable

  # S3 configuration
  cors_allowed_origins      = ["*"]
}
