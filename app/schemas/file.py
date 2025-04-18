"""File Pydantic schemas."""

from datetime import datetime

from pydantic import UUID4, BaseModel


# Shared properties
class FileBase(BaseModel):
    """Base File schema with common attributes.

    Attributes:
        filename: Original filename.
        content_type: MIME type of the file.
        size_bytes: File size in bytes.
        description: Optional description of the file.
        is_public: Whether the file is publicly accessible.
    """

    filename: str
    content_type: str
    size_bytes: int
    description: str | None = None
    is_public: bool = False


# Properties to receive via API on creation
class FileCreate(FileBase):
    """Schema for creating a new file.

    This schema is used when uploading file metadata.
    """


# Properties to receive via API on update
class FileUpdate(BaseModel):
    """Schema for updating a file.

    All fields are optional to allow partial updates.

    Attributes:
        filename: Original filename (optional).
        description: File description (optional).
        is_public: Whether the file is publicly accessible (optional).
    """

    filename: str | None = None
    description: str | None = None
    is_public: bool | None = None


# Properties shared by models stored in DB
class FileInDBBase(FileBase):
    """Base schema for file stored in database.

    Attributes:
        id: Unique identifier for the file.
        s3_key: Key in the S3 bucket where the file is stored.
        owner_id: ID of the user who owns the file.
        created_at: When the file was created.
        updated_at: When the file was last updated.
    """

    id: UUID4
    s3_key: str
    owner_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


# Properties to return via API
class File(FileInDBBase):
    """Schema for file data returned via API."""


# Additional schemas
class FileUploadResponse(BaseModel):
    """Schema for the response from a file upload request.

    Attributes:
        upload_url: Presigned URL for uploading the file to S3.
        file_id: ID of the file in the database.
    """

    upload_url: str
    file_id: UUID4


class FileDownloadResponse(BaseModel):
    """Schema for the response from a file download request.

    Attributes:
        download_url: Presigned URL for downloading the file from S3.
        filename: Original filename.
        content_type: MIME type of the file.
    """

    download_url: str
    filename: str
    content_type: str
