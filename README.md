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

   # Save the token for later use
   TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```

3. **User Information**:
   ```bash
   # Get the current user information
   curl -X 'GET' 'http://localhost:8000/api/v1/users/me' \
     -H 'Authorization: Bearer $TOKEN'
   ```

4. **Upload a File**:
   ```bash
   # Get a presigned URL for uploading
   curl -X 'POST' 'http://localhost:8000/api/v1/files/upload' \
     -H 'Authorization: Bearer $TOKEN' \
     -H 'Content-Type: application/json' \
     -d '{
       "filename": "test.txt",
       "content_type": "text/plain",
       "size_bytes": 42,
       "description": "Test file",
       "is_public": true
     }'

   # Use the returned upload_url to upload the file directly to S3
   curl -X 'PUT' '[upload_url]' \
     -H 'Content-Type: text/plain' \
     --data-binary @test.txt
   ```

5. **List Files**:
   ```bash
   # Get a list of all files
   curl -X 'GET' 'http://localhost:8000/api/v1/files' \
     -H 'Authorization: Bearer $TOKEN'
   ```

6. **Download a File**:
   ```bash
   # Get a presigned URL for downloading
   curl -X 'GET' 'http://localhost:8000/api/v1/files/download/[file_id]' \
     -H 'Authorization: Bearer $TOKEN'

   # Use the returned download_url to download the file
   curl -X 'GET' '[download_url]' -o downloaded_file.txt
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

## AWS Free Tier Utilization

This project is carefully designed to operate within AWS Free Tier limits:
- **EC2**: t2.micro instance for hosting the application
- **RDS**: db.t3.micro PostgreSQL instance with minimal storage
- **S3**: Standard storage staying below the free tier threshold
- **ALB**: Minimal configuration with optimization for cost

## License

[MIT](LICENSE)
