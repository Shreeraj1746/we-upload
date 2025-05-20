"""
User router with CRUD endpoints.

This module defines the user-related API endpoints for the application.

Endpoints:
    POST /users/ : Create a new user. Only accessible by superusers.

Details:
    - The root path ("") for the router means the endpoint will be mounted at the base path specified when including this router in the main application.
    - The create_user endpoint allows superusers to create new users, ensuring no duplicate emails exist.
    - Raises HTTP 400 if a user with the provided email already exists.
"""


from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_active_superuser, get_current_active_user
from app.models.user import User as UserModel
from app.schemas.user import (
    User as UserSchema,
    UserCreate,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter()


@router.get("", response_model=list[UserSchema])
def read_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: UserModel = Depends(get_current_active_superuser),
) -> list[UserModel]:
    """Retrieve users.

    Only superusers can access this endpoint.

    Args:
        db: Database session.
        skip: Number of records to skip (for pagination).
        limit: Maximum number of records to return (for pagination).
        current_user: The current superuser.

    Returns:
        List of users.
    """
    user_service = UserService(db)
    users = user_service.get_multi(skip=skip, limit=limit)
    return users


@router.post("", response_model=UserSchema)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: UserModel = Depends(get_current_active_superuser),
) -> UserModel:
    """Create a new user.

    Only superusers can access this endpoint.

    Args:
        db: Database session.
        user_in: New user data.
        current_user: The current superuser.

    Returns:
        The created user.

    Raises:
        HTTPException: If a user with the same email already exists.
    """
    user_service = UserService(db)
    user = user_service.get_by_email(email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists",
        )
    user = user_service.create(obj_in=user_in)
    return user


@router.get("/me", response_model=UserSchema)
def read_user_me(
    current_user: UserModel = Depends(get_current_active_user),
) -> UserModel:
    """Get current user.

    Args:
        current_user: The current user.

    Returns:
        Current user information.
    """
    return current_user


@router.put("/me", response_model=UserSchema)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    password: str = Body(None),
    full_name: str = Body(None),
    email: EmailStr = Body(None),
    current_user: UserModel = Depends(get_current_active_user),
) -> UserModel:
    """Update current user.

    Args:
        db: Database session.
        password: New password (optional).
        full_name: New full name (optional).
        email: New email (optional).
        current_user: The current user.

    Returns:
        Updated user information.
    """
    user_service = UserService(db)
    current_user_data = jsonable_encoder(current_user)
    user_in = UserUpdate(**current_user_data)
    if password is not None:
        user_in.password = password
    if full_name is not None:
        user_in.full_name = full_name
    if email is not None:
        user_in.email = email
    user = user_service.update(db_obj=current_user, obj_in=user_in)
    return user


@router.get("/{user_id}", response_model=UserSchema)
def read_user_by_id(
    user_id: str = Path(...),
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserModel:
    """Get a specific user by ID.

    Args:
        user_id: The ID of the user to retrieve.
        current_user: The current user.
        db: Database session.

    Returns:
        The requested user.

    Raises:
        HTTPException: If the user doesn't exist or the current user
        doesn't have permission to view it.
    """
    user_service = UserService(db)
    user = user_service.get(id=user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Only superusers can access other users"
        )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: str = Path(...),
    user_in: UserUpdate,
    current_user: UserModel = Depends(get_current_active_superuser),
) -> UserModel:
    """Update a user.

    Only superusers can access this endpoint.

    Args:
        db: Database session.
        user_id: The ID of the user to update.
        user_in: Updated user data.
        current_user: The current superuser.

    Returns:
        The updated user.

    Raises:
        HTTPException: If the user doesn't exist.
    """
    user_service = UserService(db)
    user = user_service.get(id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    user = user_service.update(db_obj=user, obj_in=user_in)
    return user
