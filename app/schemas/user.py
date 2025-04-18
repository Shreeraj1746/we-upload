"""User Pydantic schemas."""

from datetime import datetime

from pydantic import UUID4, BaseModel, EmailStr


# Shared properties
class UserBase(BaseModel):
    """Base User schema with common attributes.

    Attributes:
        email: User's email address.
        full_name: User's full name (optional).
        is_active: Whether the user account is active.
        is_superuser: Whether the user has superuser privileges.
    """

    email: EmailStr
    full_name: str | None = None
    is_active: bool = True
    is_superuser: bool = False


# Properties to receive via API on creation
class UserCreate(UserBase):
    """Schema for creating a new user.

    Attributes:
        password: User's password.
    """

    password: str


# Properties to receive via API on update
class UserUpdate(BaseModel):
    """Schema for updating a user.

    All fields are optional to allow partial updates.

    Attributes:
        password: User's password (optional).
    """

    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    """Base schema for user stored in database.

    Attributes:
        id: Unique identifier for the user.
        created_at: When the user was created.
        updated_at: When the user was last updated.
    """

    id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


# Properties to return via API
class User(UserInDBBase):
    """Schema for user data returned via API."""


# Properties stored in DB
class UserInDB(UserInDBBase):
    """Schema for user stored in database, including hashed password.

    Attributes:
        hashed_password: Hashed password for the user.
    """

    hashed_password: str
