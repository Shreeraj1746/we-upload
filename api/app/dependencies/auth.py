"""Authentication dependencies for FastAPI routes."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenPayload
from app.services.user_service import UserService

# OAuth2 compatible Bearer token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get the current user based on the JWT token.

    Args:
        db: Database session.
        token: JWT token from the Authorization header.

    Returns:
        The current user.

    Raises:
        HTTPException: If the token is invalid or the user doesn't exist.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_service = UserService(db)
    user = user_service.get(id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user.

    Args:
        current_user: The current user.

    Returns:
        The current active user.

    Raises:
        HTTPException: If the user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_superuser(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active superuser.

    Args:
        current_user: The current user.

    Returns:
        The current active superuser.

    Raises:
        HTTPException: If the user is not a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
