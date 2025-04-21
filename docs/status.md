# Project Status

## Current Progress
- Repository structure initialized
- FastAPI application code implemented with:
  - User and file models
  - Authentication with JWT
  - File metadata CRUD operations
  - Presigned URL generation for uploads and downloads
- Local development environment set up with Docker Compose
- User authentication system implemented
- File upload/download endpoints implemented via presigned URLs
- Database models and relationships established
- CI with GitHub Actions:
  - Comprehensive CI workflow with linting, testing, and Docker build stages
  - Terraform validation integrated in CI pipeline
  - terraform-docs added to CI environment for documentation checks
- Pre-commit hooks configured for code quality enforcement:
  - Python linting with Ruff
  - Terraform formatting, validation, and documentation
  - Git commit message validation
- System architecture diagram added to implementation plan document
- Project structure reorganized:
  - Moved Dockerfile and pyproject.toml to top level
  - Moved app directory from api/app to top level
  - Switched from hatchling to setuptools for more reliable builds
  - Added proper package configuration and basic tests
  - Updated CI workflow to use simplified dependency installation
  - Updated docker-compose.yml to reflect the new structure
  - Updated README.md with the correct directory structure
- Linting configuration improved:
  - Added appropriate rule exceptions for FastAPI-specific patterns
  - Fixed docstring format issues
  - Fixed class method parameter name issues
  - Restored Terraform checks to ensure infrastructure quality
  - Temporarily disabled strict linting rules for gradual code cleanup
  - Added exceptions for Python 3.9 typing compatibility (FA100)
  - Updated to target Python 3.13
- Development setup improved:
  - Added comprehensive development guide (docs/development.md)
  - Enhanced error handling with virtual environment checks
  - Upgraded project to use Python 3.13
- Documentation expanded:
  - Created FastAPI guide explaining how FastAPI works in this project (docs/fastapi_guide.md)
  - Created Pydantic guide explaining data validation and schema management (docs/pydantic_guide.md)

## Recently Completed
- Fixed authentication mechanism
- Updated README with proper token usage instructions
- Added comprehensive implementation plan
- Fixed MinIO S3 integration for local development
- Fixed hostname resolution issue in presigned URLs
- Fixed UUID type handling in database queries
- Fixed file download functionality
- Added FastAPI guide documentation explaining project structure and implementation
- Added Pydantic guide explaining data validation, SQLAlchemy integration, and schema design

## Known Issues and Troubleshooting

### Authentication Issues
1. **Variable Expansion in Shell Commands**
   - When using environment variables (like $TOKEN) in curl commands, always use double quotes (`"`) instead of single quotes (`'`) to allow variable expansion.
   - Example:
     ```bash
     # CORRECT (variable will be expanded):
     curl -H "Authorization: Bearer $TOKEN" 'http://localhost:8000/api/v1/users/me'

     # INCORRECT (variable will not be expanded):
     curl -H 'Authorization: Bearer $TOKEN' 'http://localhost:8000/api/v1/users/me'
     ```

2. **Token Format and Expiration**
   - Ensure you're using the complete token including the full JWT string
   - The default token expiration is set to 30 days
   - If your token has expired, simply request a new one

### UUID Type Handling
1. **Type Mismatch Between UUID and String**
   - PostgreSQL requires explicit type casting when comparing UUID and string types
   - The application now handles this automatically by ensuring:
     - UUIDs are converted to strings before database comparisons
     - Methods accept both UUID and string types for IDs
     - No more `operator does not exist: character varying = uuid` errors
   - Fixed in all methods including:
     - `get_multi_by_owner` for listing files
     - `get` for retrieving a single file
     - `create` for storing file metadata
     - `remove` for deleting files
   - If you still encounter type errors, ensure all ID values are properly converted to strings

### S3 Integration Issues
1. **MinIO Configuration**
   - When using MinIO locally as an S3 alternative, make sure the endpoint URL is properly configured
   - The boto3 client needs both the endpoint_url parameter and path-style addressing:
     ```python
     boto3.client(
         "s3",
         endpoint_url="http://minio:9000",
         config=boto3.session.Config(s3={'addressing_style': 'path'})
     )
     ```
   - If you get "InvalidAccessKeyId" errors, verify the credentials match between your API and MinIO

2. **Hostname Resolution**
   - When using MinIO in Docker, the generated presigned URLs will contain `minio:9000` hostname
   - This needs to be replaced with `localhost:9000` for clients outside the Docker network
   - The application now does this automatically in debug mode:
     ```python
     if settings.DEBUG and "minio:9000" in upload_url:
         upload_url = upload_url.replace("minio:9000", "localhost:9000")
     ```
   - If you still see "Could not resolve host: minio" errors, restart the API container

3. **File Upload/Download**
   - Test file upload with a small file first to verify S3 integration
   - For debugging, check MinIO logs: `docker-compose logs -f minio`
   - Ensure the MinIO bucket was properly created during initialization

### Docker Related Issues
1. **Container Initialization**
   - On first run, allow a few seconds for the database to initialize
   - Check container logs if endpoints aren't responding: `docker-compose logs -f api`

2. **Database Connection**
   - Verify database connection with: `curl http://localhost:8000/health/db`
   - If connection is failing, try restarting the containers: `docker-compose restart`

## Next Steps
- Add unit and integration tests
- Set up monitoring with CloudWatch
- Implement CI/CD for multiple environments
- Add API documentation
- Create a simple frontend application
- Fix remaining type checking and linting issues
- Gradually address linting issues that were temporarily disabled
- Update type annotations to use Python 3.13's improved syntax
- Begin implementing AWS infrastructure with Terraform
- Set up CI/CD pipeline with GitHub Actions
- Implement monitoring and observability solutions
- Add file versioning and advanced sharing features

## Implementation Checklist
- [x] Set up basic FastAPI application structure
- [x] Implement database models and relationships
- [x] Create authentication system
- [x] Implement file upload/download via presigned URLs
- [ ] Set up AWS infrastructure with Terraform
- [ ] Configure CI/CD pipeline
- [ ] Implement monitoring and observability
- [ ] Add advanced features (versioning, sharing, etc.)

## Completed Items
- Project structure creation
- Documentation setup
- FastAPI application setup
- Database models and schemas creation
- API endpoints implementation
- Docker and Docker Compose setup
- GitHub Actions workflow setup
- Pre-commit hooks installation and configuration
- System architecture diagram creation and documentation
- Project restructuring to adhere to standard Python package format
- GitHub Actions CI pipeline improvements
- Linting configuration improvements
- Basic type checking fixes
- Development environment documentation

## Issues
- Type checking errors need to be addressed systematically
- Linting issues need to be addressed gradually after getting a stable CI pipeline
