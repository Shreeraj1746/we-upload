"""User service for user operations."""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for user operations.

    Attributes:
        db: Database session.
    """

    def __init__(self, db: Session):
        """Initialize the user service.

        Args:
            db: Database session.
        """
        self.db = db

    def get(self, id: str) -> UserModel | None:
        """Get a user by ID.

        Args:
            id: User ID.

        Returns:
            The user with the given ID or None if not found.
        """
        return self.db.query(UserModel).filter(UserModel.id == id).first()

    def get_by_email(self, email: str) -> UserModel | None:
        """Get a user by email.

        Args:
            email: User email.

        Returns:
            The user with the given email or None if not found.
        """
        return self.db.query(UserModel).filter(UserModel.email == email).first()

    def get_multi(self, skip: int = 0, limit: int = 100) -> list[UserModel]:
        """Get multiple users.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of users.
        """
        return self.db.query(UserModel).offset(skip).limit(limit).all()

    def create(self, obj_in: UserCreate) -> UserModel:
        """Create a new user.

        Args:
            obj_in: User creation data.

        Returns:
            The created user.
        """
        db_obj = UserModel(
            id=str(uuid.uuid4()),
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_superuser=obj_in.is_superuser,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: UserModel, obj_in: UserUpdate | dict[str, Any]) -> UserModel:
        """Update a user.

        Args:
            db_obj: Existing user object from the database.
            obj_in: User update data or dictionary with fields to update.

        Returns:
            The updated user.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        for field in update_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def remove(self, id: str) -> UserModel | None:
        """Remove a user.

        Args:
            id: ID of the user to remove.

        Returns:
            The removed user or None if not found.
        """
        user = self.db.query(UserModel).filter(UserModel.id == id).first()
        if not user:
            return None
        self.db.delete(user)
        self.db.commit()
        return user

    def authenticate(self, email: str, password: str) -> UserModel | None:
        """Authenticate a user.

        Args:
            email: User email.
            password: User password.

        Returns:
            The authenticated user or None if authentication fails.
        """
        user = self.get_by_email(email=email)
        if not user:
            return None
        if not verify_password(password, str(user.hashed_password)):
            return None
        return user

    def is_active(self, user: UserModel) -> bool:
        """Check if a user is active.

        Args:
            user: User to check.

        Returns:
            True if the user is active, False otherwise.
        """
        return bool(user.is_active)

    def is_superuser(self, user: UserModel) -> bool:
        """Check if a user is a superuser.

        Args:
            user: User to check.

        Returns:
            True if the user is a superuser, False otherwise.
        """
        return bool(user.is_superuser)
