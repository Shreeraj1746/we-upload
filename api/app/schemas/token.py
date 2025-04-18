"""Token Pydantic schemas."""

from typing import Optional

from pydantic import BaseModel, UUID4


class Token(BaseModel):
    """
    Schema for authentication token.

    Attributes:
        access_token: JWT token for authenticating requests.
        token_type: Type of token (Bearer).
    """

    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """
    Schema for token payload.

    Attributes:
        sub: Subject of the token (user ID).
        exp: Expiration time of the token.
    """

    sub: Optional[str] = None
    exp: Optional[int] = None
