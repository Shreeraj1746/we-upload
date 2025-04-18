"""File upload and download router."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.file import File, FileCreate, FileUpdate, FileUploadResponse, FileDownloadResponse
from app.services.file_service import FileService

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
def create_upload_url(
    file_info: FileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileUploadResponse:
    """
    Create a presigned URL for uploading a file to S3.

    This endpoint generates a presigned URL that the client can use to upload
    a file directly to S3, bypassing the API server for the actual file data.

    Args:
        file_info: Information about the file to be uploaded.
        db: Database session.
        current_user: The authenticated user making the request.

    Returns:
        A response containing the upload URL and file ID.

    Raises:
        HTTPException: If there's an error generating the upload URL.
    """
    file_service = FileService(db)
    try:
        return file_service.create_upload_url(file_info=file_info, user=current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")


@router.get("/download/{file_id}", response_model=FileDownloadResponse)
def create_download_url(
    file_id: uuid.UUID = Path(..., description="The ID of the file to download"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileDownloadResponse:
    """
    Create a presigned URL for downloading a file from S3.

    This endpoint generates a presigned URL that the client can use to download
    a file directly from S3, bypassing the API server for the actual file data.

    Args:
        file_id: The ID of the file to download.
        db: Database session.
        current_user: The authenticated user making the request.

    Returns:
        A response containing the download URL, filename, and content type.

    Raises:
        HTTPException: If the file doesn't exist or the user doesn't have access to it.
    """
    file_service = FileService(db)
    try:
        return file_service.create_download_url(file_id=file_id, user=current_user)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not enough permissions to access this file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")


@router.get("", response_model=List[File])
def list_files(
    skip: int = Query(0, ge=0, description="Number of files to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of files to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[File]:
    """
    List files owned by the current user.

    Args:
        skip: Number of records to skip (for pagination).
        limit: Maximum number of records to return (for pagination).
        db: Database session.
        current_user: The authenticated user making the request.

    Returns:
        A list of files owned by the user.
    """
    file_service = FileService(db)
    return file_service.get_multi_by_owner(owner_id=current_user.id, skip=skip, limit=limit)


@router.get("/{file_id}", response_model=File)
def get_file(
    file_id: uuid.UUID = Path(..., description="The ID of the file to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> File:
    """
    Get a specific file by ID.

    Args:
        file_id: The ID of the file to retrieve.
        db: Database session.
        current_user: The authenticated user making the request.

    Returns:
        The requested file information.

    Raises:
        HTTPException: If the file doesn't exist or the user doesn't have access to it.
    """
    file_service = FileService(db)
    file = file_service.get(id=file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if not file.is_public and file.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions to access this file")
    return file


@router.put("/{file_id}", response_model=File)
def update_file(
    file_id: uuid.UUID,
    file_in: FileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> File:
    """
    Update a file's metadata.

    Args:
        file_id: The ID of the file to update.
        file_in: The updated file data.
        db: Database session.
        current_user: The authenticated user making the request.

    Returns:
        The updated file information.

    Raises:
        HTTPException: If the file doesn't exist or the user doesn't have access to it.
    """
    file_service = FileService(db)
    file = file_service.get(id=file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if file.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions to modify this file")

    file = file_service.update(db_obj=file, obj_in=file_in)
    return file


@router.delete("/{file_id}", response_model=File)
def delete_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> File:
    """
    Delete a file.

    This deletes both the file metadata from the database and the actual file from S3.

    Args:
        file_id: The ID of the file to delete.
        db: Database session.
        current_user: The authenticated user making the request.

    Returns:
        The deleted file information.

    Raises:
        HTTPException: If the file doesn't exist or the user doesn't have access to it.
    """
    file_service = FileService(db)
    file = file_service.get(id=file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    if file.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions to delete this file")

    try:
        file = file_service.remove(id=file_id)
        return file
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
