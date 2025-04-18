"""Module for declaring SQLAlchemy relationships after models are defined.

This module avoids circular imports by importing all models first,
then setting up relationships between them.
"""

from sqlalchemy.orm import relationship

from app.models.file import File
from app.models.user import User


def setup_relationships() -> None:
    """Set up relationships between models.

    This function must be called during application startup after all models are loaded.
    It sets up the relationship between User and File models to avoid circular imports.
    """
    # Set up the relationship between User and File
    User.files = relationship("File", back_populates="owner")  # type: ignore
    File.owner = relationship("User", back_populates="files")  # type: ignore
