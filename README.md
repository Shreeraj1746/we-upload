# We-Upload: Multi-User File Upload & Sharing Backend

A robust, scalable backend system for file uploading and sharing, built with FastAPI, deployed with Docker, and provisioned on AWS using Terraform.

## Features

- **Secure File Upload & Storage**: Upload files directly to S3 via presigned URLs
- **File Sharing & Access Control**: Share files with specific users or groups
- **Metadata Management**: Store and retrieve file metadata
- **Cloud-Native Architecture**: Deployed on AWS (staying within Free Tier limits)
- **Fully Automated CI/CD**: Using GitHub Actions for testing, building, and deployment
- **Modern Python**: Leverages Python 3.13's latest features and type hinting

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

- Python 3.13 or higher
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

To implement the project, follow these steps:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/we-upload.git
cd we-upload

# 2. Read the implementation plan
cat docs/implementation_plan.md

# 3. Start with Phase 1 (Local Development)
# Create the directory structure first
mkdir -p app/{core,db,dependencies,models,routers,schemas,services,utils}
mkdir -p tests

# 4. Implement each section progressively
# Track your progress in docs/status.md
touch docs/status.md

# 5. Use docker-compose for local testing
docker-compose up -d
```

Each phase builds upon the previous one, allowing you to incrementally develop and test the application. The implementation plan includes learning objectives for each step to help you understand the architectural decisions and technologies used.

## AWS Free Tier Utilization

This project is carefully designed to operate within AWS Free Tier limits:
- **EC2**: t2.micro instance for hosting the application
- **RDS**: db.t3.micro PostgreSQL instance with minimal storage
- **S3**: Standard storage staying below the free tier threshold
- **ALB**: Minimal configuration with optimization for cost

## License

[MIT](LICENSE)
