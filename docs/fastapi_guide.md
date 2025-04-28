# FastAPI in We-Upload Project

## Introduction

[FastAPI](https://fastapi.tiangolo.com/) is a modern, high-performance web framework for building APIs with Python 3.8+ based on standard Python type hints. In the We-Upload project, FastAPI serves as the backbone for our backend API, providing a robust foundation for building a multi-user file upload and sharing platform.

This guide explains how FastAPI is implemented in the We-Upload project and how its key components work together.

## Key Features of FastAPI Used in This Project

- **Fast**: High performance, on par with NodeJS and Go
- **Type Hints**: Leverages Python's type hints for validation, auto-documentation, and IDE support
- **Automatic API Documentation**: Generates interactive API documentation (OpenAPI/Swagger)
- **Dependency Injection**: Makes code modular and testable
- **Security and Authentication**: Built-in support for OAuth2 with JWT tokens

## Project Structure

In We-Upload, the FastAPI application follows a modular structure:

```
app/
├── core/             # Core settings and configuration
├── db/               # Database integration
├── dependencies/     # Dependency injection components
├── models/           # SQLAlchemy database models (ORM)
├── routers/          # API endpoints by resource
├── schemas/          # Pydantic models for validation and serialization
├── services/         # Business logic layer
└── main.py           # Application entry point
```

## Component Relationships

The following diagram shows how the main components interact:

```
┌───────────┐     ┌───────────┐     ┌───────────┐
│  Routers  │────▶│  Services │────▶│ SQLAlchemy│
│ (API      │     │ (Business │     │  Models   │
│  Endpoints)│◀────│  Logic)   │◀────│ (Database)│
└───────────┘     └───────────┘     └───────────┘
      │                 │                 │
      │                 │                 │
      ▼                 ▼                 ▼
┌───────────────────────────────────────────┐
│             Pydantic Schemas              │
│  (Request/Response Validation & Formats)  │
└───────────────────────────────────────────┘
```

## 1. Models

Models in this project refer to SQLAlchemy ORM models that define the database structure. They represent tables in the database and include relationships between tables.

### Key Models

**User Model** (`app/models/user.py`):
- Represents user accounts in the system
- Contains fields like `id`, `email`, `hashed_password`, `is_active`, `is_superuser`
- Mapped to the "user" table in the database

**File Model** (`app/models/file.py`):
- Stores metadata about uploaded files
- Contains fields like `id`, `filename`, `s3_key`, `content_type`, `size_bytes`, `owner_id`
- Mapped to the "file" table in the database
- Contains a relationship to the User model (owner of the file)

### Example: File Model

```python
class File(Base):
    """File model for storing file metadata."""

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False)
    s3_key = Column(String(255), nullable=False, unique=True)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    owner_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
```

Models define the database structure but are not directly exposed through the API.

## 2. Schemas

Schemas (also called Pydantic models) define data validation, serialization, and documentation. They work with FastAPI's type system to:

1. Validate incoming request data
2. Define the structure of API responses
3. Convert between API representations and database models
4. Generate API documentation automatically

### Schema Patterns

The project follows these schema patterns:

- **Base**: Common attributes shared by all schemas of a resource
- **Create**: Attributes required when creating a resource
- **Update**: Attributes that can be updated (usually all optional)
- **InDBBase**: Attributes of the resource as stored in the database
- **Response**: Attributes returned to clients via the API

### Example: File Schemas

```python
# Base schema with common attributes
class FileBase(BaseModel):
    filename: str
    content_type: str
    size_bytes: int
    description: Optional[str] = None  # Using typing.Optional
    is_public: bool = False

# Schema for creating a new file
class FileCreate(FileBase):
    pass

# Schema for updating a file (all optional)
class FileUpdate(BaseModel):
    filename: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

# Schema for file stored in database
class FileInDBBase(FileBase):
    id: UUID4
    s3_key: str
    owner_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Schema for file data returned via API
class File(FileInDBBase):
    pass
```

### Special Purpose Schemas

The project also uses special-purpose schemas for specific operations:

```python
# For generating presigned upload URLs
class FileUploadResponse(BaseModel):
    upload_url: str
    file_id: UUID4

# For generating presigned download URLs
class FileDownloadResponse(BaseModel):
    download_url: str
    filename: str
    content_type: str
```

## 3. Routers

Routers organize API endpoints by resource or functionality. They define:

- URL paths and HTTP methods
- Request and response models
- Dependencies like authentication and database access
- Path, query, and body parameters
- Status codes and error handling

### Key Routers

- **login.py**: Authentication and token generation
- **users.py**: User registration, profiles, and management
- **files.py**: File metadata and presigned URL operations
- **health.py**: Health check endpoints for monitoring

### Example: Files Router

```python
@router.post("/upload", response_model=FileUploadResponse)
def create_upload_url(
    file_info: FileCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> FileUploadResponse:
    """Create a presigned URL for uploading a file to S3."""
    file_service = FileService(db)
    try:
        return file_service.create_upload_url(file_info=file_info, user=current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {e!s}")

@router.get("", response_model=List[File])  # Using List from typing
def list_files(
    skip: int = Query(0, ge=0, description="Number of files to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of files to return"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> List[File]:
    """List all files owned by the current user."""
    file_service = FileService(db)
    owner_id_str = str(current_user.id)
    try:
        files = file_service.get_multi_by_owner(owner_id=owner_id_str, skip=skip, limit=limit)
        return [File.model_validate(file) for file in files]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {e}")
```

## 4. Services

The service layer contains the business logic of the application, separating it from the API endpoints:

```python
class FileService:
    """Service for managing file operations."""

    def __init__(self, db: Session):
        self.db = db
        # Initialize S3 client
        if settings.DEBUG:
            # Local development with MinIO
            self.s3_client = boto3.client(
                "s3",
                endpoint_url="http://minio:9000",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                config=boto3.session.Config(signature_version="s3v4"),
            )
        else:
            # Production AWS
            self.s3_client = boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )

    def create_upload_url(self, file_info: FileCreate, user: UserModel) -> FileUploadResponse:
        """Create a new file record and generate a presigned upload URL."""
        # Generate a unique S3 key
        s3_key = f"{user.id}/{uuid.uuid4()}/{file_info.filename}"

        # Create file metadata record
        file_in_db = FileModel(
            filename=file_info.filename,
            s3_key=s3_key,
            content_type=file_info.content_type,
            size_bytes=file_info.size_bytes,
            description=file_info.description,
            is_public=file_info.is_public,
            owner_id=user.id,
        )
        self.db.add(file_in_db)
        self.db.commit()
        self.db.refresh(file_in_db)

        # Generate presigned URL for upload
        upload_url = self.s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": s3_key,
                "ContentType": file_info.content_type,
            },
            ExpiresIn=settings.PRESIGNED_URL_EXPIRATION,
        )

        return FileUploadResponse(upload_url=upload_url, file_id=file_in_db.id)
```

## 5. API Endpoints

API endpoints are organized around resources:

### Authentication Endpoints

- `POST /login/token`: Obtain a JWT access token
- `POST /login/test-token`: Test token validity

### User Endpoints

- `POST /api/v1/users/`: Create a new user
- `GET /api/v1/users/`: List users (admin only)
- `GET /api/v1/users/me`: Get current user profile
- `GET /api/v1/users/{user_id}`: Get user by ID
- `PUT /api/v1/users/{user_id}`: Update user

### File Endpoints

- `POST /api/v1/files/upload`: Get presigned URL for uploading
- `GET /api/v1/files/download/{file_id}`: Get presigned URL for downloading
- `GET /api/v1/files`: List files owned by the current user
- `GET /api/v1/files/{file_id}`: Get file details
- `PUT /api/v1/files/{file_id}`: Update file metadata
- `DELETE /api/v1/files/{file_id}`: Delete a file

### Health Check Endpoints

- `GET /health`: Basic health check
- `GET /health/db`: Database connection check

## FastAPI Integration Patterns

### 1. Dependency Injection

The project uses FastAPI's dependency injection system to inject:

- Database sessions
- Current authenticated user
- Configuration settings
- Service classes

Example:
```python
@router.get("/{file_id}", response_model=File)
def get_file(
    file_id: uuid.UUID = Path(..., description="The ID of the file to retrieve"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> File:
    # Use injected dependencies
    file_service = FileService(db)
    file = file_service.get(id=file_id)
    # ...
```

### 2. Service Layer

The project uses a service layer pattern to separate business logic from API endpoints:

- **Routers**: Handle HTTP request/response
- **Services**: Implement business logic
- **Models**: Represent database entities

Example:
```python
# Router uses service
@router.post("/upload", response_model=FileUploadResponse)
def create_upload_url(...):
    file_service = FileService(db)
    return file_service.create_upload_url(file_info=file_info, user=current_user)

# Service implements logic
def create_upload_url(self, file_info: FileCreate, user: UserModel) -> FileUploadResponse:
    # Implementation details
    # ...
```

### 3. Error Handling

The project uses FastAPI's `HTTPException` for error handling:

```python
if not file:
    raise HTTPException(status_code=404, detail="File not found")
if file.owner_id != current_user.id and not current_user.is_superuser:
    raise HTTPException(status_code=403, detail="Not enough permissions to access this file")
```

## Project-Specific FastAPI Features

### 1. Presigned URL Generation

Instead of handling file uploads directly, the API generates presigned URLs to allow direct upload/download to/from S3:

```python
def create_upload_url(self, file_info: FileCreate, user: UserModel) -> FileUploadResponse:
    # Register file metadata
    file = self.create(obj_in=file_info, owner_id=user.id)

    # Generate presigned URL
    upload_url = self.s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": file.s3_key,
            "ContentType": file.content_type,
        },
        ExpiresIn=settings.PRESIGNED_URL_EXPIRATION,
    )

    # Return upload URL and file ID
    return FileUploadResponse(upload_url=upload_url, file_id=file.id)
```

### 2. JWT Authentication

The project uses JWT tokens for authentication:

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/token")

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> UserModel:
    # Decode and validate token
    # ...
    return user
```

## Further Reading

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [JWT Authentication](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
