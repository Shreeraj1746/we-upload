"""File service for file operations."""

import uuid
from typing import Any, Dict, List, Optional, Union

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file import File
from app.models.user import User
from app.schemas.file import FileCreate, FileUpdate, FileUploadResponse, FileDownloadResponse


class FileService:
    """
    Service for file operations.

    This service handles file metadata CRUD operations and generates
    presigned URLs for direct file upload/download to/from S3.

    Attributes:
        db: Database session.
        s3_client: Boto3 S3 client.
    """

    def __init__(self, db: Session):
        """
        Initialize the file service.

        Args:
            db: Database session.
        """
        self.db = db
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    def get(self, id: uuid.UUID) -> Optional[File]:
        """
        Get a file by ID.

        Args:
            id: File ID.

        Returns:
            The file with the given ID or None if not found.
        """
        return self.db.query(File).filter(File.id == id).first()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[File]:
        """
        Get multiple files.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of files.
        """
        return self.db.query(File).offset(skip).limit(limit).all()

    def get_multi_by_owner(
        self, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[File]:
        """
        Get multiple files by owner.

        Args:
            owner_id: Owner's ID.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of files owned by the specified user.
        """
        return (
            self.db.query(File)
            .filter(File.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, obj_in: FileCreate, owner_id: uuid.UUID) -> File:
        """
        Create a new file metadata record.

        Args:
            obj_in: File creation data.
            owner_id: ID of the file owner.

        Returns:
            The created file metadata record.
        """
        file_id = uuid.uuid4()
        s3_key = f"{owner_id}/{file_id}/{obj_in.filename}"

        db_obj = File(
            id=str(file_id),
            filename=obj_in.filename,
            s3_key=s3_key,
            content_type=obj_in.content_type,
            size_bytes=obj_in.size_bytes,
            description=obj_in.description,
            is_public=obj_in.is_public,
            owner_id=str(owner_id),
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: File, obj_in: Union[FileUpdate, Dict[str, Any]]) -> File:
        """
        Update a file's metadata.

        Args:
            db_obj: Existing file object from the database.
            obj_in: File update data or dictionary with fields to update.

        Returns:
            The updated file metadata record.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field in update_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def remove(self, id: uuid.UUID) -> Optional[File]:
        """
        Remove a file.

        This removes both the file metadata from the database and
        the actual file from S3.

        Args:
            id: ID of the file to remove.

        Returns:
            The removed file metadata record or None if not found.

        Raises:
            Exception: If there's an error deleting the file from S3.
        """
        file_obj = self.db.query(File).filter(File.id == id).first()
        if not file_obj:
            return None

        # Delete file from S3
        try:
            self.s3_client.delete_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=file_obj.s3_key,
            )
        except ClientError as e:
            # Log the error but continue with metadata deletion
            print(f"Error deleting file from S3: {e}")

        # Delete metadata from database
        self.db.delete(file_obj)
        self.db.commit()
        return file_obj

    def create_upload_url(self, file_info: FileCreate, user: User) -> FileUploadResponse:
        """
        Create a presigned URL for file upload and register the file metadata.

        Args:
            file_info: Information about the file to be uploaded.
            user: The user uploading the file.

        Returns:
            A response containing the upload URL and file ID.

        Raises:
            Exception: If there's an error generating the presigned URL.
        """
        # Create file metadata
        file_obj = self.create(obj_in=file_info, owner_id=uuid.UUID(user.id))

        # Generate presigned URL for upload
        try:
            upload_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': settings.S3_BUCKET_NAME,
                    'Key': file_obj.s3_key,
                    'ContentType': file_info.content_type,
                },
                ExpiresIn=settings.PRESIGNED_URL_EXPIRY,
            )
            return FileUploadResponse(
                upload_url=upload_url,
                file_id=uuid.UUID(file_obj.id),
            )
        except ClientError as e:
            # If URL generation fails, clean up the metadata
            self.db.delete(file_obj)
            self.db.commit()
            raise Exception(f"Error generating presigned URL: {e}")

    def create_download_url(self, file_id: uuid.UUID, user: User) -> FileDownloadResponse:
        """
        Create a presigned URL for file download.

        Args:
            file_id: ID of the file to download.
            user: The user requesting the download.

        Returns:
            A response containing the download URL, filename, and content type.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            PermissionError: If the user doesn't have permission to access the file.
            Exception: If there's an error generating the presigned URL.
        """
        # Get file metadata
        file_obj = self.get(id=file_id)
        if not file_obj:
            raise FileNotFoundError(f"File with ID {file_id} not found")

        # Check permissions
        if not file_obj.is_public and file_obj.owner_id != user.id and not user.is_superuser:
            raise PermissionError("Not enough permissions to access this file")

        # Generate presigned URL for download
        try:
            download_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.S3_BUCKET_NAME,
                    'Key': file_obj.s3_key,
                },
                ExpiresIn=settings.PRESIGNED_URL_EXPIRY,
            )
            return FileDownloadResponse(
                download_url=download_url,
                filename=file_obj.filename,
                content_type=file_obj.content_type,
            )
        except ClientError as e:
            raise Exception(f"Error generating presigned URL: {e}")
