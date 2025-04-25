resource "aws_security_group" "ec2_sg" {
  name        = "${var.project_name}-ec2-sg"
  description = "Security group for EC2 instances"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH access"
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "${var.project_name}-ec2-sg"
  }
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-ec2-profile"
  role = var.ec2_role_name
}

resource "aws_instance" "api_server" {
  ami                         = var.ami_id
  instance_type               = "t2.micro" # Free tier eligible
  subnet_id                   = var.public_subnet_id
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  key_name                    = var.ssh_key_name
  iam_instance_profile        = aws_iam_instance_profile.ec2_profile.name
  associate_public_ip_address = true

  user_data = <<-EOF
              #!/bin/bash -xe
              # Log all output to a file for debugging
              exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

              echo "Starting EC2 initialization..."

              # Update and install dependencies
              apt-get update -y
              apt-get install -y git python3-pip python3-venv python3-dev awscli nginx postgresql postgresql-contrib

              # Clone the repository
              git clone https://github.com/Shreeraj1746/we-upload.git /app
              cd /app

              # Fix config.py to avoid circular reference
              CONFIG_FILE="/app/app/core/config.py"
              sed -i 's|return "postgresql://postgres:postgres@db:5432/we_upload"|return "postgresql://\$\{POSTGRES_USER\}:\$\{POSTGRES_PASSWORD\}@\$\{POSTGRES_SERVER\}:\$\{POSTGRES_PORT\}/\$\{POSTGRES_DB\}"|' $CONFIG_FILE
              sed -i 's/POSTGRES_SERVER: str = "db"/POSTGRES_SERVER: str = "localhost"/' $CONFIG_FILE

              # Create a PostgreSQL user and database
              sudo -u postgres psql -c "CREATE DATABASE ${var.db_name};"
              sudo -u postgres psql -c "CREATE USER ${var.db_username} WITH PASSWORD '${var.db_password}';"
              sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${var.db_name} TO ${var.db_username};"
              sudo -u postgres psql -c "ALTER USER ${var.db_username} WITH SUPERUSER;"

              # Create Python virtual environment
              python3 -m venv /app/venv
              source /app/venv/bin/activate

              # Install dependencies
              pip install --upgrade pip
              pip install -e .
              pip install boto3 uvicorn

              # Create environment file with AWS production settings
              cat > /app/.env << EOL
              WE_UPLOAD_DEBUG=false
              WE_UPLOAD_AWS_REGION=${var.aws_region}
              WE_UPLOAD_S3_BUCKET_NAME=${var.s3_bucket_name}
              WE_UPLOAD_USE_INSTANCE_ROLE=true
              WE_UPLOAD_POSTGRES_SERVER=localhost
              WE_UPLOAD_POSTGRES_USER=${var.db_username}
              WE_UPLOAD_POSTGRES_PASSWORD=${var.db_password}
              WE_UPLOAD_POSTGRES_DB=${var.db_name}
              WE_UPLOAD_FIRST_SUPERUSER=admin@example.com
              WE_UPLOAD_FIRST_SUPERUSER_PASSWORD=admin
              WE_UPLOAD_SECRET_KEY=$(openssl rand -base64 32)
              EOL

              # Set environment variables
              set -a
              source /app/.env
              set +a

              # Initialize the database
              cd /app
              python -c "
              try:
                from app.db.base import Base
                from app.db.session import engine
                Base.metadata.create_all(bind=engine)
                print('Database tables created successfully')
              except Exception as e:
                print(f'Error creating database tables: {e}')
              "

              # Create systemd service for the application
              cat > /etc/systemd/system/weupload.service << EOL
              [Unit]
              Description=We-Upload FastAPI Application
              After=network.target postgresql.service

              [Service]
              User=ubuntu
              Group=ubuntu
              WorkingDirectory=/app
              EnvironmentFile=/app/.env
              ExecStart=/app/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
              Restart=always

              [Install]
              WantedBy=multi-user.target
              EOL

              # Set permissions and start service
              chown -R ubuntu:ubuntu /app
              systemctl daemon-reload
              systemctl enable weupload
              systemctl start weupload

              # Configure Nginx as reverse proxy
              cat > /etc/nginx/sites-available/we-upload << EOL
              server {
                listen 80;
                server_name _;

                location / {
                  proxy_pass http://localhost:8000;
                  proxy_set_header Host \$host;
                  proxy_set_header X-Real-IP \$remote_addr;
                  proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
                  proxy_set_header X-Forwarded-Proto \$scheme;
                }
              }
              EOL

              # Enable the site
              ln -s /etc/nginx/sites-available/we-upload /etc/nginx/sites-enabled/
              rm -f /etc/nginx/sites-enabled/default
              systemctl restart nginx

              echo "EC2 initialization complete"
              EOF

  tags = {
    Name = "${var.project_name}-api-server"
  }

  root_block_device {
    volume_size = 8     # 8GB is within free tier limits
    volume_type = "gp2" # General Purpose SSD
    encrypted   = true
  }
}
