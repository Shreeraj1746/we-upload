"""Token Pydantic schemas."""

from pydantic import BaseModel


class Token(BaseModel):
    """Schema for authentication token.

    Attributes:
        access_token: JWT token for authenticating requests.
        token_type: Type of token (Bearer).
    """

    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """Schema for token payload.

    Attributes:
        sub: Subject of the token (user ID).
        exp: Expiration time of the token.
    """

    sub: str | None = None
    exp: int | None = None
