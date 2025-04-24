"""File service for file operations."""

import uuid
from typing import Any

import boto3
from botocore.exceptions import ClientError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file import File as FileModel
from app.models.user import User as UserModel
from app.schemas.file import FileCreate, FileDownloadResponse, FileUpdate, FileUploadResponse


class FileService:
    """Service for file operations.

    This service handles file metadata CRUD operations and generates
    presigned URLs for direct file upload/download to/from S3.

    Attributes:
        db: Database session.
        s3_client: Boto3 S3 client.
    """

    def __init__(self, db: Session):
        """Initialize the file service.

        Args:
            db: Database session.
        """
        self.db = db

        # Configure S3 client
        if settings.DEBUG:
            # Local development with MinIO
            self.s3_client = boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url="http://minio:9000",  # MinIO service in docker-compose
                # Use path-style instead of virtual-hosted style (required for MinIO)
                config=boto3.session.Config(s3={"addressing_style": "path"}),
            )
            self.s3_bucket_name = settings.S3_BUCKET_NAME
            self.is_local_dev = True
        else:
            # Production AWS configuration
            # Create a configuration with signature version 4, required for all regions
            s3_config = boto3.session.Config(
                signature_version="s3v4", region_name=settings.AWS_REGION
            )

            # In production, if USE_INSTANCE_ROLE is True, don't pass explicit credentials
            # This allows boto3 to use the EC2 instance role or environment variables
            if settings.USE_INSTANCE_ROLE:
                self.s3_client = boto3.client(
                    "s3", region_name=settings.AWS_REGION, config=s3_config
                )
            else:  # noqa: PLR5501
                # Otherwise, use the provided credentials (for testing or non-EC2 environments)
                # Skip MinIO default credentials
                if (
                    settings.AWS_ACCESS_KEY_ID != "minio"
                    and settings.AWS_SECRET_ACCESS_KEY != "minio123"  # noqa: S105
                ):
                    self.s3_client = boto3.client(
                        "s3",
                        region_name=settings.AWS_REGION,
                        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                        config=s3_config,
                    )
                else:
                    # Fallback without credentials - boto3 will check environment variables and instance role
                    self.s3_client = boto3.client(
                        "s3", region_name=settings.AWS_REGION, config=s3_config
                    )

            self.s3_bucket_name = settings.S3_BUCKET_NAME
            self.is_local_dev = False

    def get(self, id: uuid.UUID | str) -> FileModel | None:
        """Get a file by ID.

        Args:
            id: File ID (can be UUID or string).

        Returns:
            The file with the given ID or None if not found.
        """
        # Convert ID to string to match database column type
        file_id = str(id) if isinstance(id, uuid.UUID) else id
        return self.db.query(FileModel).filter(FileModel.id == file_id).first()

    def get_multi(self, skip: int = 0, limit: int = 100) -> list[FileModel]:
        """Get multiple files.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of files.
        """
        return self.db.query(FileModel).offset(skip).limit(limit).all()

    def get_multi_by_owner(
        self, owner_id: uuid.UUID | str, skip: int = 0, limit: int = 100
    ) -> list[FileModel]:
        """Get multiple files by owner.

        Args:
            owner_id: Owner's ID (can be UUID or string).
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of files owned by the specified user.
        """
        # Convert UUID to string if it's a UUID object
        owner_id_str = str(owner_id) if isinstance(owner_id, uuid.UUID) else owner_id

        return (
            self.db.query(FileModel)
            .filter(FileModel.owner_id == owner_id_str)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, obj_in: FileCreate, owner_id: uuid.UUID | str) -> FileModel:
        """Create a new file metadata record.

        Args:
            obj_in: File creation data.
            owner_id: ID of the file owner (can be UUID or string).

        Returns:
            The created file metadata record.
        """
        file_id = uuid.uuid4()
        # Ensure owner_id is a string
        owner_id_str = str(owner_id)
        s3_key = f"{owner_id_str}/{file_id}/{obj_in.filename}"

        db_obj = FileModel(
            id=str(file_id),
            filename=obj_in.filename,
            s3_key=s3_key,
            content_type=obj_in.content_type,
            size_bytes=obj_in.size_bytes,
            description=obj_in.description,
            is_public=obj_in.is_public,
            owner_id=owner_id_str,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: FileModel, obj_in: FileUpdate | dict[str, Any]) -> FileModel:
        """Update a file's metadata.

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

    def remove(self, id: uuid.UUID | str) -> FileModel | None:
        """Remove a file.

        This removes both the file metadata from the database and
        the actual file from S3.

        Args:
            id: ID of the file to remove (can be UUID or string).

        Returns:
            The removed file metadata record or None if not found.

        Raises:
            Exception: If there's an error deleting the file from S3.
        """
        # Convert ID to string to match database column type
        file_id = str(id) if isinstance(id, uuid.UUID) else id
        file_obj = self.db.query(FileModel).filter(FileModel.id == file_id).first()
        if not file_obj:
            return None

        # Delete file from S3
        try:
            self.s3_client.delete_object(
                Bucket=self.s3_bucket_name,
                Key=file_obj.s3_key,
            )
        except ClientError as e:
            # Log the error but continue with metadata deletion
            print(f"Error deleting file from S3: {e}")

        # Delete metadata from database
        self.db.delete(file_obj)
        self.db.commit()
        return file_obj

    def create_upload_url(self, file_info: FileCreate, user: UserModel) -> FileUploadResponse:
        """Create a presigned URL for file upload and register the file metadata.

        Args:
            file_info: Information about the file to be uploaded.
            user: The user uploading the file.

        Returns:
            A response containing the upload URL and file ID.

        Raises:
            Exception: If there's an error generating the presigned URL.
        """
        # Create file metadata
        # Pass the user.id directly as a string to avoid type conversion issues
        file_obj = self.create(obj_in=file_info, owner_id=user.id)

        # Generate presigned URL for upload
        try:
            params = {
                "Bucket": self.s3_bucket_name,
                "Key": file_obj.s3_key,
                "ContentType": file_info.content_type,
            }

            # Generate the presigned URL for upload
            upload_url = self.s3_client.generate_presigned_url(
                "put_object",
                Params=params,
                ExpiresIn=settings.PRESIGNED_URL_EXPIRY,
            )

            # For local development, replace 'minio' hostname with 'localhost'
            # This is necessary because the client machine can't resolve the Docker hostname
            if self.is_local_dev and "minio:9000" in upload_url:
                upload_url = upload_url.replace("minio:9000", "localhost:9000")

            return FileUploadResponse(
                upload_url=upload_url,
                file_id=uuid.UUID(str(file_obj.id)),
            )
        except ClientError as e:
            # If URL generation fails, clean up the metadata
            self.db.delete(file_obj)
            self.db.commit()
            raise Exception(f"Error generating presigned URL: {e}")

    def create_download_url(self, file_id: uuid.UUID, user: UserModel) -> FileDownloadResponse:
        """Create a presigned URL for file download.

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
            params = {
                "Bucket": self.s3_bucket_name,
                "Key": file_obj.s3_key,
            }

            # Generate the presigned URL for download
            download_url = self.s3_client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=settings.PRESIGNED_URL_EXPIRY,
            )

            # For local development, replace 'minio' hostname with 'localhost'
            # This is necessary because the client machine can't resolve the Docker hostname
            if self.is_local_dev and "minio:9000" in download_url:
                download_url = download_url.replace("minio:9000", "localhost:9000")

            return FileDownloadResponse(
                download_url=download_url,
                filename=str(file_obj.filename),
                content_type=str(file_obj.content_type),
            )
        except ClientError as e:
            raise Exception(f"Error generating presigned URL: {e}")
