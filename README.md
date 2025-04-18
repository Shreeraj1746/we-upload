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
├── api/                    # FastAPI application code
│   ├── app/                # Application package
│   │   ├── core/           # Core components (config, security)
│   │   ├── db/             # Database models and connection
│   │   ├── dependencies/   # FastAPI dependencies
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routers/        # API endpoints
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── Dockerfile          # Docker configuration for API
│   └── tests/              # API tests
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
├── docker-compose.yml      # Local development setup
└── docs/                   # Documentation
    └── implementation_plan.md  # Step-by-step guide
```

## Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/we-upload.git
cd we-upload

# Start local services
docker-compose up -d

# API will be available at http://localhost:8000
# Documentation at http://localhost:8000/docs
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
