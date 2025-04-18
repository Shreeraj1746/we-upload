"""User database model."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base

if TYPE_CHECKING:
    from .file import File  # noqa: F401


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

    id = Column(String(36), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active: bool = Column(Boolean(), default=True)
    is_superuser: bool = Column(Boolean(), default=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    files = relationship("File", back_populates="owner")
