"""User database model."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:
    from .file import File


class User(Base):
    """User model for storing user information.

    Attributes:
        id: Unique identifier for the user.
        email: User's email address (unique).
        full_name: User's full name.
        hashed_password: Hashed password for the user.
        is_active: Whether the user account is active.
        is_superuser: Whether the user has superuser privileges.
        created_at: When the user was created.
        updated_at: When the user was last updated.
        files: Files owned by the user.
    """

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean(), default=True)  # type: ignore
    is_superuser = Column(Boolean(), default=False)  # type: ignore
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Define attributes that will be populated by relationship later
    files: list[File] = []


# User-File relationship is defined in a central location to avoid circular dependencies.
# This means that instead of each module importing the other directly (which can cause import errors),
# a single module manages the relationship, making dependencies clearer and the codebase easier to maintain.
