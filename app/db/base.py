"""Database base module for importing all models.

This module is used by Alembic to generate migrations.
"""

# Import all the models, so that Alembic can detect them
from app.db.base_class import Base  # noqa
from app.models.file import File  # noqa
from app.models.user import User  # noqa
