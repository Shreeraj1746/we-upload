"""SQLAlchemy session management module."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create the SQLAlchemy engine
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create a SessionLocal class for database connections
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> sessionmaker:
    """
    Get a database session.

    This function is used as a dependency in FastAPI endpoints.

    Yields:
        A SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
