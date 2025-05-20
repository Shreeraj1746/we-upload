"""File database model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user import User  # noqa: F401


class File(Base):
    """File model for storing file metadata.

    Attributes:
        id: Unique identifier for the file.
        filename: Original filename.
        s3_key: Key in the S3 bucket where the file is stored.
        content_type: MIME type of the file.
        size_bytes: File size in bytes.
        description: Optional description of the file.
        is_public: Whether the file is publicly accessible.
        owner_id: ID of the user who owns the file.
        created_at: When the file was created.
        updated_at: When the file was last updated.
        owner: The user who owns the file.
    """

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    filename = Column(String(255), nullable=False)
    s3_key = Column(String(255), nullable=False, unique=True)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)
    owner_id = Column(String(36), ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Define attributes that will be populated by SQLAlchemy relationships later.
    # These attributes are not actual database columns, but are set up using SQLAlchemy's
    # relationship() function in other parts of the codebase (typically in the User model).
    # When SQLAlchemy loads a File instance, it can automatically populate these attributes
    # with related objects (such as the owner User) based on foreign key relationships.
    owner = None
