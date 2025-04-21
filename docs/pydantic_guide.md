# Pydantic in We-Upload Project

## Introduction to Pydantic

[Pydantic](https://docs.pydantic.dev/) is a data validation and settings management library using Python type annotations. In the We-Upload project, Pydantic plays a critical role in:

1. **Data Validation**: Ensuring incoming data meets specific requirements
2. **Request/Response Modeling**: Defining the structure of API inputs and outputs
3. **Settings Management**: Providing a robust way to handle configuration
4. **Schema Documentation**: Auto-generating OpenAPI documentation

## Why We Use Pydantic

### 1. Type Safety and Validation

Pydantic uses Python's type hints to validate data at runtime. This provides several benefits:

- **Early Error Detection**: Data validation errors are caught at the API boundary rather than deep in the application logic
- **Self-Documenting Code**: Type hints serve as documentation that can't become outdated
- **IDE Support**: Better autocomplete, refactoring, and error detection in development

### 2. Automatic Documentation

When combined with FastAPI, Pydantic models automatically generate:

- OpenAPI schemas
- Interactive API documentation
- Client-side type definitions

### 3. Clean Conversion Between Formats

Pydantic makes it easy to:
- Convert JSON to Python objects
- Convert between SQLAlchemy models and API schemas
- Transform data between different representations

### 4. Reduced Boilerplate

Without Pydantic, we would need to write extensive validation code for each API endpoint. Pydantic handles:
- Type checking
- Default values
- Complex validations
- Format conversions

## Pydantic and SQLAlchemy Integration

In We-Upload, we use a clear separation between:

1. **SQLAlchemy Models**: Define database structure (tables, columns, relationships)
2. **Pydantic Schemas**: Define API contracts (requests, responses)

### Integration Pattern

We use the `from_attributes` configuration in our Pydantic models to enable direct conversion from SQLAlchemy models:

```python
class FileInDBBase(FileBase):
    """Base schema for file stored in database."""
    id: UUID4
    s3_key: str
    owner_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # This enables conversion from SQLAlchemy
```

This allows us to convert between SQLAlchemy models and Pydantic schemas using:

```python
# Convert SQLAlchemy model to Pydantic schema
file_model = file_service.get(id=file_id)  # SQLAlchemy model
file_schema = File.model_validate(file_model)  # Pydantic schema
return file_schema  # Return to client
```

### Schema Hierarchy

Our project uses a consistent schema hierarchy pattern:

```
                           ┌─────────┐
                           │ BaseModel│
                           └─────────┘
                                 │
                                 ▼
                          ┌────────────┐
                          │ EntityBase │ (common attributes)
                          └────────────┘
                        /        │        \
                       /         │         \
         ┌────────────┐  ┌─────────────┐  ┌────────────────┐
         │ EntityCreate│  │EntityUpdate │  │ EntityInDBBase │
         └────────────┘  └─────────────┘  └────────────────┘
                                                    │
                                                    ▼
                                             ┌────────────┐
                                             │   Entity   │ (API response)
                                             └────────────┘
```

## Without Pydantic vs. With Pydantic

### Example 1: Input Validation

#### Without Pydantic:

```python
@router.post("/upload")
def create_upload_url(request: Request):
    # Manual validation
    data = await request.json()

    # Check if required fields exist
    if "filename" not in data:
        raise HTTPException(status_code=400, detail="Missing filename")
    if "content_type" not in data:
        raise HTTPException(status_code=400, detail="Missing content type")
    if "size_bytes" not in data:
        raise HTTPException(status_code=400, detail="Missing size_bytes")

    # Type validation
    if not isinstance(data["filename"], str):
        raise HTTPException(status_code=400, detail="filename must be a string")
    if not isinstance(data["content_type"], str):
        raise HTTPException(status_code=400, detail="content_type must be a string")
    if not isinstance(data["size_bytes"], int):
        raise HTTPException(status_code=400, detail="size_bytes must be an integer")

    # Additional validations (size limits, etc.)
    if len(data["filename"]) > 255:
        raise HTTPException(status_code=400, detail="Filename too long")
    if data["size_bytes"] <= 0:
        raise HTTPException(status_code=400, detail="Size must be positive")

    # Finally process the data
    file_service.create_upload_url(
        filename=data["filename"],
        content_type=data["content_type"],
        size_bytes=data["size_bytes"],
        description=data.get("description"),
        is_public=data.get("is_public", False),
        user=current_user
    )
```

#### With Pydantic:

```python
@router.post("/upload", response_model=FileUploadResponse)
def create_upload_url(
    file_info: FileCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> FileUploadResponse:
    """Create a presigned URL for uploading a file to S3."""
    file_service = FileService(db)
    return file_service.create_upload_url(file_info=file_info, user=current_user)
```

### Example 2: Converting Database Model to API Response

#### Without Pydantic:

```python
@router.get("/{file_id}")
def get_file(file_id: str, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    # Get the file
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Manual conversion to dict
    response = {
        "id": str(file.id),  # Convert UUID to string
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": file.size_bytes,
        "description": file.description,
        "is_public": file.is_public,
        "owner_id": str(file.owner_id),  # Convert UUID to string
        "created_at": file.created_at.isoformat(),  # Format datetime
        "updated_at": file.updated_at.isoformat(),
        # Must remember to add any new fields here!
    }

    return response
```

#### With Pydantic:

```python
@router.get("/{file_id}", response_model=File)
def get_file(
    file_id: uuid.UUID = Path(..., description="The ID of the file to retrieve"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> File:
    """Get a specific file by ID."""
    file_service = FileService(db)
    file = file_service.get(id=file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    return File.model_validate(file)  # Automatic conversion with validation
```

### Benefits of Using Pydantic

1. **Reduced Boilerplate**: 20+ lines of validation code reduced to 1 line
2. **Centralized Schema Definition**: Define once, use everywhere
3. **Automatic Documentation**: Schemas are reflected in the OpenAPI docs
4. **Consistent Error Handling**: Validation errors have a consistent format
5. **Type Safety**: IDE support for autocompletion and error checking

## Real-World Examples from We-Upload

### 1. File Schema Hierarchy

```python
# Base with common attributes
class FileBase(BaseModel):
    """Base File schema with common attributes."""
    filename: str
    content_type: str
    size_bytes: int
    description: str | None = None
    is_public: bool = False

# Creation schema
class FileCreate(FileBase):
    """Schema for creating a new file."""
    pass

# Update schema with optional fields
class FileUpdate(BaseModel):
    """Schema for updating a file."""
    filename: str | None = None
    description: str | None = None
    is_public: bool | None = None

# Database schema with additional fields
class FileInDBBase(FileBase):
    """Base schema for file stored in database."""
    id: UUID4
    s3_key: str
    owner_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# API response schema
class File(FileInDBBase):
    """Schema for file data returned via API."""
    pass
```

### 2. Special Purpose Schemas

```python
class FileUploadResponse(BaseModel):
    """Schema for the response from a file upload request."""
    upload_url: str
    file_id: UUID4

class FileDownloadResponse(BaseModel):
    """Schema for the response from a file download request."""
    download_url: str
    filename: str
    content_type: str
```

### 3. Settings Management

```python
class Settings(BaseSettings):
    """Application settings."""
    PROJECT_NAME: str = "We-Upload"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    # Database settings
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: str | None = None

    # AWS settings
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str
    PRESIGNED_URL_EXPIRATION: int = 3600  # 1 hour

    # CORS settings
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    # Debug mode
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
            )
```

## Common Pydantic Patterns in We-Upload

### 1. Field Validation

```python
class UserCreate(UserBase):
    """Schema for creating a new user."""
    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=8)  # Requires minimum length
```

### 2. Computed Fields

```python
class User(UserInDBBase):
    """Schema for user data returned via API."""
    @validator("id", "created_at", "updated_at", pre=True)
    def default_datetime_utc(cls, value):
        """Convert datetime fields to UTC."""
        if isinstance(value, datetime):
            return value.replace(tzinfo=timezone.utc)
        return value
```

### 3. Type Conversion

```python
class Token(BaseModel):
    """Schema for JWT token."""
    access_token: str
    token_type: str = "bearer"

    @validator("access_token")
    def token_must_be_valid_jwt(cls, v):
        """Validate token format."""
        try:
            jwt.decode(v, settings.SECRET_KEY, algorithms=["HS256"])
            return v
        except jwt.PyJWTError:
            raise ValueError("Invalid token format")
```

## Why it Would Not Be a Great Idea to Skip Pydantic

1. **Inconsistent Validation**: Without Pydantic, validation logic would be scattered across endpoints
2. **Error-Prone Schema Changes**: Adding a field would require updating multiple places
3. **Documentation Issues**: No automatic API documentation
4. **Repetitive Code**: Manual validation and conversion would be duplicated
5. **Harder Testing**: Testing validation logic in isolation would be more complex
6. **Type Safety Loss**: No static type checking for request/response models

## Additional Resources

- [Official Pydantic Documentation](https://docs.pydantic.dev/)
- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [FastAPI with Pydantic](https://fastapi.tiangolo.com/tutorial/body/#pydantic-models)
- [SQLAlchemy with Pydantic](https://docs.pydantic.dev/latest/usage/models/#helper-functions)
- [Type Annotations Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [Pydantic Field Types](https://docs.pydantic.dev/latest/usage/types/)
- [Pydantic Validators](https://docs.pydantic.dev/latest/usage/validators/)
- [Advanced Pydantic Usage](https://docs.pydantic.dev/latest/usage/models/)
