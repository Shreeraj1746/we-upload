"""Database base module for importing all models.

This module is used by Alembic to generate migrations.
"""

# Import the base class first
from app.db.base_class import Base  # noqa

# Import models in the correct order to avoid circular dependencies
# Import model classes without relationships
from app.models.user import User
from app.models.file import File

# Add type annotations to help mypy
FileModel = File
UserModel = User
