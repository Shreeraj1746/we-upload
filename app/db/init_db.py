"""Database initialization module."""

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal, engine
from app.models.user import User as UserModel
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialize the database.

    Creates the database tables if they don't exist.
    """
    # Create db tables
    # Import Base from base module to ensure all models are properly registered
    from app.db.base import Base
    from app.db.relations import setup_relationships

    # Setup relationships between models
    setup_relationships()

    logger.info("Creating database tables")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Create superuser if configured
    if settings.FIRST_SUPERUSER and settings.FIRST_SUPERUSER_PASSWORD:
        create_first_superuser()


def create_first_superuser() -> None:
    """Create an initial superuser in the database.

    This function is called on application startup and creates a superuser
    if settings.FIRST_SUPERUSER and settings.FIRST_SUPERUSER_PASSWORD are set.
    """
    db = SessionLocal()
    try:
        # Check if superuser exists
        if (
            settings.FIRST_SUPERUSER
            and settings.FIRST_SUPERUSER_PASSWORD
            and not _user_exists(db, email=settings.FIRST_SUPERUSER)
        ):
            user_in = UserCreate(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                full_name="Initial Superuser",
                is_superuser=True,
            )
            user = _create_user(db, obj_in=user_in)
            logger.info(f"Superuser created: {user.email}")
        else:
            logger.info("Superuser already exists. Skipping creation.")
    except Exception as e:
        logger.error(f"Error creating superuser: {e}")
    finally:
        db.close()


def _user_exists(db: Session, email: str) -> bool:
    """Check if a user with the given email exists.

    Args:
        db: Database session.
        email: Email to check.

    Returns:
        True if user exists, False otherwise.
    """
    return db.query(UserModel).filter(UserModel.email == email).first() is not None


def _create_user(db: Session, obj_in: UserCreate) -> UserModel:
    """Create a new user in the database.

    Args:
        db: Database session.
        obj_in: User data.

    Returns:
        The created user object.
    """
    # Create user object from schema
    db_obj = UserModel(
        email=obj_in.email,
        hashed_password=get_password_hash(obj_in.password),
        full_name=obj_in.full_name,
        is_superuser=obj_in.is_superuser,
    )
    # Add to database
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
