# We-Upload: Multi-User File Upload & Sharing Backend

A robust, scalable backend system for file uploading and sharing, built with FastAPI, deployed with Docker, and provisioned on AWS using Terraform.

## Features

- **Secure File Upload & Storage**: Upload files directly to S3 via presigned URLs
- **File Sharing & Access Control**: Share files with specific users or groups
- **Metadata Management**: Store and retrieve file metadata
- **Cloud-Native Architecture**: Deployed on AWS (staying within Free Tier limits)
- **Fully Automated CI/CD**: Using GitHub Actions for testing, building, and deployment

## Repository Structure

```
.
├── app/                    # FastAPI application code
│   ├── core/               # Core components (config, security)
│   ├── db/                 # Database models and connection
│   ├── dependencies/       # FastAPI dependencies
│   ├── models/             # SQLAlchemy models
│   ├── routers/            # API endpoints
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   └── utils/              # Utilities
├── terraform/              # Infrastructure as Code
│   ├── environments/       # Environment-specific configs
│   │   ├── dev/            # Development environment
│   │   └── prod/           # Production environment
│   └── modules/            # Reusable Terraform modules
│       ├── alb/            # Application Load Balancer
│       ├── ecs/            # ECS Cluster and Service
│       ├── iam/            # IAM Roles and Policies
│       ├── monitoring/     # CloudWatch and Monitoring
│       ├── rds/            # RDS PostgreSQL Database
│       ├── s3/             # S3 Buckets
│       ├── security/       # Security Groups, KMS
│       └── vpc/            # VPC, Subnets, Routes
├── .github/                # GitHub configuration
│   └── workflows/          # GitHub Actions workflows
├── docs/                   # Documentation
│   └── implementation_plan.md  # Step-by-step guide
├── tests/                  # API tests
├── docker-compose.yml      # Local development setup
├── Dockerfile              # Docker configuration for API
└── pyproject.toml          # Python project configuration
```

## Local Development

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- Terraform (for infrastructure deployment)

```bash
# Clone the repository
git clone https://github.com/yourusername/we-upload.git
cd we-upload

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Start local services
docker-compose up -d

# API will be available at http://localhost:8000
# Documentation at http://localhost:8000/docs
```

## Running Tests

The project includes comprehensive testing to ensure functionality:

### Unit Tests

Unit tests verify individual components of the application without external dependencies:

```bash
# Activate your virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run unit tests
pytest --cov=app --exclude-dir=tests/test_basic_file_api.py
```

### API Integration Tests

API integration tests verify that the application's endpoints work correctly with a real database and S3 storage:

```bash
# Activate your virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run API integration tests
# This will automatically spin up Docker Compose with all required services
pytest tests/test_basic_file_api.py -v
```

The integration tests:
- Automatically start Docker Compose with all services (API, PostgreSQL, MinIO)
- Wait for all services to be healthy
- Run tests against the API endpoints
- Clean up after completion

### CI/CD Pipeline

Tests run automatically on every push to the repository via GitHub Actions:
1. **Linting**: Code style and quality checks using ruff and pre-commit hooks
2. **Unit Tests**: Core functionality tests
3. **API Integration Tests**: End-to-end tests of the API functionality
4. **Build**: Docker image build (on main branch only)

## Manual Testing

### Setting Up the Local Environment

```bash
# Clone the repository if you haven't already
git clone https://github.com/yourusername/we-upload.git
cd we-upload

# Start the local development environment
docker-compose up -d

# Wait for services to initialize
# This may take a few seconds
```

### Initialize the Database

The database tables need to be created on first run:

```bash
# Execute a command in the API container to initialize the database
docker exec -it we-upload-api-1 python -c "from app.db.base import Base; from app.db.session import engine; Base.metadata.create_all(bind=engine)"
```

### Current Status and Known Issues

The application has been fixed and is now working properly. The previous issues have been resolved:

1. **Database Relationship Issue**: Fixed the circular dependency between User and File models by:
   - Moving relationship definitions to a separate module
   - Setting up relationships after both models are fully defined
   - Using proper UUID generation for model IDs

2. **Authentication Working**: User creation and authentication now work correctly:
   - Database tables are created automatically on startup
   - Initial superuser is created automatically
   - Login endpoint returns valid JWT tokens

3. **MinIO S3 Integration**: Fixed the integration with local MinIO for file storage:
   - Added proper endpoint URL configuration in the S3 client
   - Set path-style addressing for MinIO compatibility
   - Implemented debug mode detection for local development
   - Fixed hostname resolution for presigned URLs (replacing 'minio:9000' with 'localhost:9000')

4. **UUID Type Handling**: Fixed database type mismatches between UUID and string types:
   - Ensured consistent type conversion before database operations
   - Added support for both UUID and string ID parameters
   - Fixed the "operator does not exist: character varying = uuid" error when listing files
   - Fixed file download functionality that was affected by the same issue

### Testing API Endpoints

Now you can test the complete application functionality:

1. **Test Health Endpoints**:

   ```bash
   # Check API health
   curl http://localhost:8000/health

   # Check database connection
   curl http://localhost:8000/health/db
   ```

2. **Authentication**:

   ```bash
   # Get an access token using the default admin credentials
   curl -X 'POST' 'http://localhost:8000/login/access-token' \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'username=admin%40example.com&password=admin'

   # The response will contain your access token
   # Copy the full token value from the response and set it as an environment variable:
   TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

   # Alternatively, you can extract the token automatically (requires jq):
   # TOKEN=$(curl -s -X 'POST' 'http://localhost:8000/login/access-token' \
   #   -H 'Content-Type: application/x-www-form-urlencoded' \
   #   -d 'username=admin%40example.com&password=admin' | jq -r '.access_token')

   # Verify the token is set correctly:
   echo $TOKEN
   ```

   > **Note:** When using the token in curl commands, make sure to use **double quotes** for the Authorization header
   > (e.g., `-H "Authorization: Bearer $TOKEN"`) so that the shell expands the $TOKEN variable.
   > Single quotes would prevent variable expansion.

3. **User Information**:

   ```bash
   # Get the current user information
   curl -X 'GET' 'http://localhost:8000/api/v1/users/me' \
     -H "Authorization: Bearer $TOKEN"
   ```

4. **Upload a File**:

   ```bash
   # First, create a sample test file
   echo "This is a test file" > test.txt

   # Get a presigned URL for uploading
   UPLOAD_RESPONSE=$(curl -s -X 'POST' 'http://localhost:8000/api/v1/files/upload' \
     -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{
       "filename": "test.txt",
       "content_type": "text/plain",
       "size_bytes": 42,
       "description": "Test file",
       "is_public": true
     }')

   # Extract the upload URL and file ID (requires jq)
   # If you don't have jq, you can manually copy these values from the response
   UPLOAD_URL=$(echo $UPLOAD_RESPONSE | jq -r '.upload_url')
   FILE_ID=$(echo $UPLOAD_RESPONSE | jq -r '.file_id')

   echo "Upload URL: $UPLOAD_URL"
   echo "File ID: $FILE_ID"

   # Upload the file using the presigned URL
   curl -X 'PUT' "$UPLOAD_URL" \
     -H 'Content-Type: text/plain' \
     --data-binary @test.txt
   ```

5. **List Files**:

   ```bash
   # Get a list of all files
   curl -X 'GET' 'http://localhost:8000/api/v1/files' \
     -H "Authorization: Bearer $TOKEN"
   ```

6. **Download a File**:

   ```bash
   # Get a presigned URL for downloading
   # Use the FILE_ID from the upload step
   DOWNLOAD_RESPONSE=$(curl -s -X 'GET' "http://localhost:8000/api/v1/files/download/$FILE_ID" \
     -H "Authorization: Bearer $TOKEN")

   # Extract the download URL (requires jq)
   DOWNLOAD_URL=$(echo "$DOWNLOAD_RESPONSE" | jq -r '.download_url')

   echo "Download URL: $DOWNLOAD_URL"

   # Download the file
   curl -X 'GET' "$DOWNLOAD_URL" -o downloaded_file.txt

   # Verify the downloaded file
   cat downloaded_file.txt
   ```

### Troubleshooting

If you encounter issues with file upload or download:

1. **Check MinIO Logs**:

   ```bash
   docker-compose logs -f minio
   ```

2. **Verify MinIO Bucket**:

   ```bash
   docker exec -it we-upload-minio-1 sh -c "mkdir -p /data/we-upload-local"
   ```

3. **Restart the Service**:

   ```bash
   docker-compose restart api
   ```

4. **Hostname Resolution**:
   If you see "Could not resolve host: minio" errors, this is because your local machine can't resolve the Docker hostname. The API has been updated to replace 'minio:9000' with 'localhost:9000' in the presigned URLs, but if you still have issues, try:

   ```bash
   # Restart the API service
   docker-compose restart api

   # Or manually replace the hostname in the URL
   FIXED_URL=$(echo $UPLOAD_URL | sed 's/minio:9000/localhost:9000/g')
   echo "Fixed URL: $FIXED_URL"
   ```

For more detailed troubleshooting information, see the `docs/status.md` file.

### Cleanup

```bash
# Stop and remove containers
docker-compose down

# To remove volumes (database data and file storage)
docker-compose down -v
```

## Deployment

This project uses Terraform to provision infrastructure on AWS and GitHub Actions for CI/CD. See the `docs/implementation_plan.md` for detailed instructions on each phase of deployment.

## Following the Implementation Plan

The project includes a comprehensive implementation plan in `docs/implementation_plan.md` that breaks down the development process into four phases:

1. **Phase 1: Local Development**
   - Set up the FastAPI application structure
   - Implement database models and integrations
   - Create file upload/download endpoints
   - Configure Docker for local development

2. **Phase 2: AWS & Terraform Setup**
   - Configure AWS account and IAM permissions
   - Build core infrastructure with Terraform
   - Set up database and compute resources
   - Integrate S3 for file storage

3. **Phase 3: CI/CD with GitHub Actions**
   - Implement automated testing
   - Create CI workflows for code quality
   - Set up deployment automation

4. **Phase 4: Monitoring & Observability**
   - Configure CloudWatch logging and metrics
   - Implement health checks and alerting
   - Optimize performance within Free Tier limits

Each phase builds upon the previous one, allowing you to incrementally develop and test the application. The implementation plan includes learning objectives for each step to help you understand the architectural decisions and technologies used.

## Learning Terraform with Checkpoint Branch

If you're starting your journey to learn Terraform, you can use the `checkpoint_2025_04_19` branch as a starting point:

```bash
# Clone the repository
git clone https://github.com/yourusername/we-upload.git
cd we-upload

# Switch to the checkpoint branch
git checkout checkpoint_2025_04_19

# Start the local development environment
docker-compose up -d
```

This branch has the local setup working correctly, with all Phase 1 tasks completed. You should be able to run all commands in the "Testing API Endpoints" section above.

From here, you can follow [Phase 2 of the implementation plan](docs/implementation_plan.md#phase-2-aws--terraform-setup) to learn and implement infrastructure as code with Terraform. This provides a hands-on approach to learning AWS resource provisioning while building on a functional application.

## AWS Free Tier Utilization

This project is carefully designed to operate within AWS Free Tier limits:

- **EC2**: t2.micro instance for hosting the application
- **RDS**: db.t3.micro PostgreSQL instance with minimal storage
- **S3**: Standard storage staying below the free tier threshold
- **ALB**: Minimal configuration with optimization for cost

## Testing AWS Deployment

After deploying the application to AWS using Terraform, you can test the file upload and download functionality using the following steps:

### Prerequisites

- An AWS account with the application deployed using Terraform (follow steps in `docs/implementation_plan.md`)
- The public IP address of the EC2 instance (available from Terraform output)
- [curl](https://curl.se/) for command-line testing or [Postman](https://www.postman.com/) for a GUI alternative
- [jq](https://jqlang.github.io/jq/) for parsing JSON responses (optional but recommended)

### Deployment Verification

After running `terraform apply`, you should see output with the EC2 instance's public IP address. Note this address for the following steps.

```bash
Outputs:

ec2_instance_public_ip = "35.154.107.233"
s3_bucket_name = "we-upload-uploads-iol8gd0b"
rds_endpoint = "we-upload-db.cr6k82agk5wq.ap-south-1.rds.amazonaws.com:5432"
```

**Note**: It may take 5-10 minutes for the EC2 instance to fully initialize. The user data script needs to install dependencies, clone the repository, and start the application.

### Testing Steps

1. **Verify Application Health**:

   ```bash
   # Check if the application is running
   curl http://<EC2_IP>/health

   # Expected response:
   # {"status":"ok","timestamp":"2025-04-24T03:32:15.123456"}

   # Check database connection
   curl http://<EC2_IP>/health/db

   # Expected response:
   # {"status":"ok","message":"Database connection successful"}
   ```

2. **Authentication**:

   ```bash
   # Get an access token using the default admin credentials
   # (replace <EC2_IP> with your EC2 instance's public IP)
   curl -X 'POST' 'http://<EC2_IP>/login/access-token' \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'username=admin@example.com&password=admin'

   # The response will contain your access token
   # Copy the full token value from the response and set it as an environment variable:
   TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```

3. **Upload a File**:

   ```bash
   # First, create a sample test file
   echo "This is a test file for AWS deployment" > aws_test.txt

   # Get a presigned URL for uploading
   # (replace <EC2_IP> with your EC2 instance's public IP)
   UPLOAD_RESPONSE=$(curl -s -X 'POST' "http://<EC2_IP>/api/v1/files/upload" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"filename": "aws_test.txt", "content_type": "text/plain", "size_bytes": 42, "description": "Test file for AWS deployment", "is_public": true}')

   # Extract the upload URL and file ID (requires jq)
   # If you don't have jq, you can manually copy these values from the response
   UPLOAD_URL=$(echo $UPLOAD_RESPONSE | grep -o 'https://[^"]*')
   FILE_ID=$(echo $UPLOAD_RESPONSE | grep -o '"file_id":"[^"]*"' | cut -d'"' -f4)

   echo "Upload URL: $UPLOAD_URL"
   echo "File ID: $FILE_ID"

   # Upload the file using the presigned URL
   curl -X 'PUT' "$UPLOAD_URL" \
     -H 'Content-Type: text/plain' \
     --data-binary @aws_test.txt
   ```

   Note: If the upload fails with an error about signature version or region, apply the fixes from the Troubleshooting section.

4. **List Files**:

   ```bash
   # Get a list of all files
   curl -X 'GET' "http://<EC2_IP>/api/v1/files" \
     -H "Authorization: Bearer $TOKEN"
   ```

5. **Download a File**:

   ```bash
   # Get a presigned URL for downloading
   # Use the FILE_ID from the upload step
   DOWNLOAD_RESPONSE=$(curl -s -X 'GET' "http://<EC2_IP>/api/v1/files/download/$FILE_ID" \
     -H "Authorization: Bearer $TOKEN")

   # Extract the download URL (requires jq)
   DOWNLOAD_URL=$(echo "$DOWNLOAD_RESPONSE" | jq -r '.download_url')

   echo "Download URL: $DOWNLOAD_URL"

   # Download the file
   curl -X 'GET' "$DOWNLOAD_URL" -o downloaded_aws_file.txt

   # Verify the downloaded file
   cat downloaded_aws_file.txt
   ```

6. **Verify File Data**:

   ```bash
   # Verify the file metadata
   curl -X 'GET' "http://<EC2_IP>/api/v1/files/$FILE_ID" \
     -H "Authorization: Bearer $TOKEN"
   ```

### Troubleshooting AWS Deployment

If you encounter issues with file upload or download in AWS:

1. **Application Initialization Issues**:

   ```bash
   # If you get 502 Bad Gateway errors, the application may still be initializing.
   # Wait 5-10 minutes after deployment, then try again.

   # To check the status of the application directly:
   ssh -i ~/.ssh/id_rsa ubuntu@<EC2_IP>

   # Once logged in, check Docker container status:
   cd /app
   sudo docker-compose ps

   # Check application logs:
   sudo docker-compose logs api
   ```

2. **502 Bad Gateway Errors**:
   If you encounter "502 Bad Gateway" errors from nginx after the initialization period, it might be due to:
   - **Database Connection Issues**: The default config had a hardcoded connection to "db" hostname, which works for local Docker Compose but not for EC2. We now install PostgreSQL locally on the EC2 instance.
   - **Circular Reference in Config**: There was a circular reference in settings initialization. We've fixed this by using default values directly.

   To manually fix these issues:

   ```bash
   # SSH into your EC2 instance
   ssh -i ~/.ssh/id_rsa ubuntu@<EC2_IP>

   # Fix database connection in config.py
   sudo sed -i 's|return "postgresql://postgres:postgres@db:5432/we_upload"|return f"postgresql://{user}:{password}@localhost:{port}/{db}"|' /app/app/core/config.py
   sudo sed -i 's/POSTGRES_SERVER: str = "db"/POSTGRES_SERVER: str = "localhost"/' /app/app/core/config.py

   # Install and configure PostgreSQL
   sudo apt-get update && sudo apt-get install -y postgresql postgresql-contrib
   sudo -u postgres psql -c "CREATE DATABASE weupload;"
   sudo -u postgres psql -c "CREATE USER weuploadadmin WITH PASSWORD 'admin';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE weupload TO weuploadadmin;"

   # Update environment variables
   echo "WE_UPLOAD_POSTGRES_SERVER=localhost" | sudo tee -a /app/.env

   # Restart the application
   sudo systemctl restart weupload
   ```

3. **Check EC2 Initialization**:

   ```bash
   # SSH into the EC2 instance
   ssh -i ~/.ssh/id_rsa ubuntu@<EC2_IP>

   # Check the cloud-init log to see if initialization completed:
   sudo cat /var/log/cloud-init-output.log
   ```

4. **S3 Region and Credentials Issues**:
   If you encounter S3 upload/download errors like "Error parsing the X-Amz-Credential parameter" or "NoSuchBucket", it might be due to:
   - **S3 Region Mismatch**: The application might be configured with a different region than where your S3 bucket is located.
   - **MinIO Credentials Used in AWS**: The default configuration uses MinIO credentials which don't work in AWS.
   - **S3 Bucket Name Mismatch**: The application might be configured with the wrong S3 bucket name.

   To fix these issues:

   ```bash
   # SSH into your EC2 instance
   ssh -i ~/.ssh/id_rsa ubuntu@<EC2_IP>

   # Check and update AWS region to match the bucket region (usually ap-south-1)
   grep WE_UPLOAD_AWS_REGION /app/.env
   sudo sed -i 's/WE_UPLOAD_AWS_REGION=wrong-region/WE_UPLOAD_AWS_REGION=ap-south-1/g' /app/.env

   # Remove explicit AWS credentials to use EC2 instance role instead
   sudo sed -i '/WE_UPLOAD_AWS_ACCESS_KEY_ID=/d' /app/.env
   sudo sed -i '/WE_UPLOAD_AWS_SECRET_ACCESS_KEY=/d' /app/.env

   # Update S3 bucket name if needed (check the Terraform output for actual name)
   sudo sed -i 's/WE_UPLOAD_S3_BUCKET_NAME=wrong-bucket-name/WE_UPLOAD_S3_BUCKET_NAME=correct-bucket-name/g' /app/.env

   # Modify the S3 client configuration to use the instance role
   sudo python3 -c "f=open('/app/app/services/file_service.py', 'r'); content=f.read(); f.close(); content=content.replace('        else:\\n            # Production AWS\\n            self.s3_client = boto3.client(\\n                \\\"s3\\\",\\n                region_name=settings.AWS_REGION,\\n                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,\\n                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,\\n            )', '        else:\\n            # Production AWS\\n            self.s3_client = boto3.client(\\n                \\\"s3\\\",\\n                region_name=settings.AWS_REGION,\\n                config=boto3.session.Config(signature_version=\\\"s3v4\\\"),\\n            )'); f=open('/app/app/services/file_service.py', 'w'); f.write(content); f.close(); print('File updated with signature_version parameter')"

   # Restart the application
   sudo systemctl restart weupload
   ```

5. **Upload a File**:

   ```bash
   # First, create a sample test file
   echo "This is a test file for AWS deployment" > aws_test.txt

   # Get a presigned URL for uploading
   # (replace <EC2_IP> with your EC2 instance's public IP)
   UPLOAD_RESPONSE=$(curl -s -X 'POST' "http://<EC2_IP>/api/v1/files/upload" \
     -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{
       "filename": "aws_test.txt",
       "content_type": "text/plain",
       "size_bytes": 42,
       "description": "Test file for AWS deployment",
       "is_public": true
     }')

   # Extract the upload URL and file ID (requires jq)
   # If you don't have jq, you can manually copy these values from the response
   UPLOAD_URL=$(echo $UPLOAD_RESPONSE | grep -o 'https://[^"]*')
   FILE_ID=$(echo $UPLOAD_RESPONSE | grep -o '"file_id":"[^"]*"' | cut -d'"' -f4)

   echo "Upload URL: $UPLOAD_URL"
   echo "File ID: $FILE_ID"

   # Upload the file using the presigned URL
   curl -X 'PUT' "$UPLOAD_URL" \
     -H 'Content-Type: text/plain' \
     --data-binary @aws_test.txt
   ```

   Note: If the upload fails with an error about signature version or region, apply the fixes from the Troubleshooting section.

6. **List Files**:

   ```bash
   # Get a list of all files
   curl -X 'GET' "http://<EC2_IP>/api/v1/files" \
     -H "Authorization: Bearer $TOKEN"
   ```

7. **Download a File**:

   ```bash
   # Get a presigned URL for downloading
   # Use the FILE_ID from the upload step
   DOWNLOAD_RESPONSE=$(curl -s -X 'GET' "http://<EC2_IP>/api/v1/files/download/$FILE_ID" \
     -H "Authorization: Bearer $TOKEN")

   # Extract the download URL (requires jq)
   DOWNLOAD_URL=$(echo "$DOWNLOAD_RESPONSE" | jq -r '.download_url')

   echo "Download URL: $DOWNLOAD_URL"

   # Download the file
   curl -X 'GET' "$DOWNLOAD_URL" -o downloaded_aws_file.txt

   # Verify the downloaded file
   cat downloaded_aws_file.txt
   ```

8. **Verify File Data**:

   ```bash
   # Verify the file metadata
   curl -X 'GET' "http://<EC2_IP>/api/v1/files/$FILE_ID" \
     -H "Authorization: Bearer $TOKEN"
   ```

## License

[MIT](LICENSE)
