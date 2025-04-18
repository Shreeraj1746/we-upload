provider "aws" {
  region = var.aws_region
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.17"
    }
  }

  backend "s3" {
    # Backend config supplied via CLI
  }

  required_version = ">= 1.5.0"
}

locals {
  name = "we-upload-${var.environment}"

  tags = {
    Project     = "we-upload"
    Environment = var.environment
    Terraform   = "true"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"

  name                       = local.name
  vpc_cidr_block             = var.vpc_cidr_block
  availability_zones         = [data.aws_availability_zones.available.names[0], data.aws_availability_zones.available.names[1]]
  public_subnet_cidr_blocks  = var.public_subnet_cidr_blocks
  private_subnet_cidr_blocks = var.private_subnet_cidr_blocks
  enable_nat_gateway         = var.environment == "prod" # Use NAT gateway only in production

  tags = local.tags
}

# S3 Module
module "s3" {
  source = "../../modules/s3"

  bucket_name          = "we-upload-files-${var.environment}-${random_id.bucket_suffix.hex}"
  cors_allowed_origins = var.cors_allowed_origins

  tags = local.tags
}

# Random suffix for unique bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# EC2 Instance for API (for free tier)
resource "aws_security_group" "api" {
  name        = "${local.name}-api-sg"
  description = "Security group for API server"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "API Port"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.tags
}

resource "aws_iam_role" "ec2_role" {
  name = "${local.name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = local.tags
}

resource "aws_iam_role_policy" "s3_access" {
  name = "${local.name}-s3-access"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          module.s3.bucket_arn,
          "${module.s3.bucket_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "api" {
  name = "${local.name}-api-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_instance" "api" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t2.micro" # Free tier eligible
  subnet_id              = module.vpc.public_subnet_ids[0]
  vpc_security_group_ids = [aws_security_group.api.id]
  iam_instance_profile   = aws_iam_instance_profile.api.name
  key_name               = var.key_name

  user_data = <<-EOF
              #!/bin/bash
              amazon-linux-extras install docker -y
              systemctl start docker
              systemctl enable docker
              docker pull ${var.ecr_repository}:${var.image_tag}
              docker run -d -p 8000:8000 \
                -e WE_UPLOAD_POSTGRES_SERVER=${aws_db_instance.postgres.address} \
                -e WE_UPLOAD_POSTGRES_USER=${var.db_username} \
                -e WE_UPLOAD_POSTGRES_PASSWORD=${var.db_password} \
                -e WE_UPLOAD_POSTGRES_DB=${var.db_name} \
                -e WE_UPLOAD_SECRET_KEY=${var.api_secret_key} \
                -e WE_UPLOAD_S3_BUCKET_NAME=${module.s3.bucket_id} \
                -e WE_UPLOAD_AWS_REGION=${var.aws_region} \
                ${var.ecr_repository}:${var.image_tag}
              EOF

  tags = merge(
    local.tags,
    {
      Name = "${local.name}-api"
    }
  )
}

# RDS PostgreSQL for database (free tier)
resource "aws_security_group" "db" {
  name        = "${local.name}-db-sg"
  description = "Security group for database"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "PostgreSQL"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.tags
}

resource "aws_db_subnet_group" "postgres" {
  name       = "${local.name}-db-subnet-group"
  subnet_ids = module.vpc.private_subnet_ids

  tags = local.tags
}

resource "aws_db_instance" "postgres" {
  identifier             = "${local.name}-db"
  engine                 = "postgres"
  engine_version         = "13"
  instance_class         = "db.t3.micro" # Free tier eligible
  allocated_storage      = 20
  storage_type           = "gp2"
  username               = var.db_username
  password               = var.db_password
  db_name                = var.db_name
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  publicly_accessible    = false
  skip_final_snapshot    = true

  tags = local.tags
}

# Latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}
