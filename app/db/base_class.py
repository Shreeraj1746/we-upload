"""SQLAlchemy base class for ORM models."""

import re
from typing import Any

from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    """Base class for all SQLAlchemy models.

    This class provides common functionality, including automated table name generation
    based on the class name.
    """

    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @declared_attr  # type: ignore
    def __tablename__(self) -> str:
        """Generate table name from class name.

        Converts CamelCase to snake_case for the table name.

        Returns:
            The table name in snake_case.
        """
        # Convert camel case to snake case
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", self.__name__).lower()
        return name
