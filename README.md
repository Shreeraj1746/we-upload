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

   # Alternatively, extract the token automatically (requires jq):
   TOKEN=$(curl -s -X 'POST' 'http://localhost:8000/login/access-token' \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'username=admin%40example.com&password=admin' | jq -r '.access_token')

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

### Local Troubleshooting

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

### Cleanup

```bash
# Stop and remove containers
docker-compose down

# To remove volumes (database data and file storage)
docker-compose down -v
```

## Deployment

This project uses Terraform to provision infrastructure on AWS and GitHub Actions for CI/CD. See the `docs/implementation_plan.md` for detailed instructions on each phase of deployment.

## AWS Deployment and Testing

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
   # {"status":"ok","service":"we-upload-api"}

   # Check database connection
   curl http://<EC2_IP>/health/db

   # Expected response:
   # {"status":"ok","database":"connected"}
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

   # Extract the upload URL and file ID
   # If you have jq installed:
   UPLOAD_URL=$(echo $UPLOAD_RESPONSE | jq -r '.upload_url')
   FILE_ID=$(echo $UPLOAD_RESPONSE | jq -r '.file_id')

   # If you don't have jq, use these grep commands instead:
   UPLOAD_URL=$(echo $UPLOAD_RESPONSE | grep -o '"upload_url":"[^"]*"' | cut -d'"' -f4)
   FILE_ID=$(echo $UPLOAD_RESPONSE | grep -o '"file_id":"[^"]*"' | cut -d'"' -f4)

   echo "Upload URL: $UPLOAD_URL"
   echo "File ID: $FILE_ID"

   # Upload the file using the presigned URL
   curl -X 'PUT' "$UPLOAD_URL" \
     -H 'Content-Type: text/plain' \
     --data-binary @aws_test.txt
   ```

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

   # Extract the download URL
   # If you have jq installed:
   DOWNLOAD_URL=$(echo "$DOWNLOAD_RESPONSE" | jq -r '.download_url')

   # If you don't have jq, use this grep command instead:
   DOWNLOAD_URL=$(echo "$DOWNLOAD_RESPONSE" | grep -o '"download_url":"[^"]*"' | cut -d'"' -f4)

   echo "Download URL: $DOWNLOAD_URL"

   # Download the file
   curl -X 'GET' "$DOWNLOAD_URL" -o downloaded_aws_file.txt

   # Verify the downloaded file
   cat downloaded_aws_file.txt
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

## Monitoring with CloudWatch

The application uses AWS CloudWatch for comprehensive monitoring and observability, providing insight into performance, health, and usage patterns.

### CloudWatch Features

1. **Structured JSON Logging**
   - All application logs are formatted as JSON for easy parsing and analysis in CloudWatch Logs
   - Log retention is configured for 7 days (AWS Free Tier friendly)
   - Log groups are automatically created during deployment

2. **System Metrics Monitoring**
   - CPU utilization from the EC2 instance
   - Memory usage (custom metric via CloudWatch agent)
   - Disk utilization (custom metric via CloudWatch agent)

3. **Automated Alerting**
   - CPU utilization alarm (triggers when CPU > 80% for 10 minutes)
   - Memory usage alarm (triggers when memory > 80% for 10 minutes)
   - Disk usage alarm (triggers when disk space > 85% for 10 minutes)

### Viewing Logs and Metrics

1. **Using AWS Console**
   - Navigate to CloudWatch > Log groups > /aws/ec2/we-upload
   - Select the log stream for your instance to view logs
   - Navigate to CloudWatch > Metrics > All metrics > CWAgent for custom metrics

2. **Using AWS CLI**
   ```bash
   # View the most recent logs
   aws logs get-log-events \
     --log-group-name "/aws/ec2/we-upload" \
     --log-stream-name "<INSTANCE_ID>/app.log" \
     --limit 10

   # Check CPU metrics for the last hour
   aws cloudwatch get-metric-statistics \
     --namespace "AWS/EC2" \
     --metric-name "CPUUtilization" \
     --dimensions Name=InstanceId,Value=<INSTANCE_ID> \
     --start-time $(date -u -v-1H +"%Y-%m-%dT%H:%M:%SZ") \
     --end-time $(date -u +"%Y-%m-%dT%H:%M:%SZ") \
     --period 300 \
     --statistics Average
   ```

### Testing CloudWatch Integration

For detailed steps on testing the CloudWatch integration, refer to `docs/cloudwatch_testing_plan.md`. This document includes:

- Procedures for verifying log delivery
- Methods to test metric collection
- Steps to validate alarm functionality
- Ways to check log retention policies
- Instructions for creating and using CloudWatch dashboards

### Extending Monitoring Capabilities

While staying within AWS Free Tier, you can:

1. **Create custom metrics** for application-specific measurements
2. **Set up composite alarms** that trigger based on multiple conditions
3. **Configure dashboard widgets** to visualize important metrics
4. **Use CloudWatch Insights** for advanced log analysis

For production environments beyond Free Tier, consider:
- Longer log retention periods
- Integration with SNS for alarm notifications
- Setting up X-Ray for distributed tracing
- Implementing enhanced metric collection at 1-minute intervals

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
- **API Gateway**: Limited to 1 million requests per month
- **CloudWatch**: Basic monitoring only

For detailed information about AWS deployment, see the [terraform README](terraform/README.md).

## License

[MIT](LICENSE)
