# EC2 Instance for API (for free tier)
resource "aws_security_group" "api" {
  name        = "${var.name}-api-sg"
  description = "Security group for API server"
  vpc_id      = var.vpc_id

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

  tags = var.tags
}

resource "aws_iam_role" "ec2_role" {
  name = "${var.name}-ec2-role"

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

  tags = var.tags
}

resource "aws_iam_role_policy" "s3_access" {
  name = "${var.name}-s3-access"
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
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "api" {
  name = "${var.name}-api-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_instance" "api" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnet_ids[0]
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
                -e WE_UPLOAD_S3_BUCKET_NAME=${var.s3_bucket_name} \
                -e WE_UPLOAD_AWS_REGION=${data.aws_region.current.name} \
                ${var.ecr_repository}:${var.image_tag}
              EOF

  tags = merge(
    var.tags,
    {
      Name = "${var.name}-api"
    }
  )
}

# RDS PostgreSQL for database (free tier)
resource "aws_security_group" "db" {
  name        = "${var.name}-db-sg"
  description = "Security group for database"
  vpc_id      = var.vpc_id

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

  tags = var.tags
}

resource "aws_db_subnet_group" "postgres" {
  name       = "${var.name}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = var.tags
}

resource "aws_db_instance" "postgres" {
  identifier             = "${var.name}-db"
  engine                 = "postgres"
  engine_version         = "13"
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  storage_type           = "gp2"
  username               = var.db_username
  password               = var.db_password
  db_name                = var.db_name
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  publicly_accessible    = false
  skip_final_snapshot    = true

  tags = var.tags
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

# Get current AWS region
data "aws_region" "current" {}
