"""
Authentication Schemas

Pydantic request/response models for the authentication API.

Design Decisions:
    - **No ``EmailStr``**: Pydantic's ``EmailStr`` requires the optional
      ``email-validator`` dependency; a strict pattern is used instead so no
      additional package is introduced.
    - **Password policy**: Minimum length of 8 characters, enforced at the
      schema boundary so invalid registrations never reach the service layer.
"""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserCreate(BaseModel):
    """Registration request payload."""

    model_config = ConfigDict(populate_by_name=True)

    email: str = Field(
        ...,
        pattern=_EMAIL_PATTERN,
        max_length=320,
        description="The user's email address (used as the login name).",
        examples=["analyst@example.com"],
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Plaintext password (minimum 8 characters).",
        examples=["correct-horse-battery"],
    )


class UserOut(BaseModel):
    """Public representation of a user — never includes secrets."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Unique user identifier.")
    email: str = Field(..., description="The user's email address.")
    is_active: bool = Field(default=True, description="Whether the account is active.")
    created_at: datetime | None = Field(
        default=None,
        description="UTC timestamp of account creation.",
    )


class Token(BaseModel):
    """OAuth2-style bearer token response."""

    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(..., description="The encoded JWT access token.")
    token_type: str = Field(default="bearer", description="Token type indicator.")


def is_valid_email(email: str) -> bool:
    """Return True when ``email`` matches the accepted email shape."""
    return re.fullmatch(_EMAIL_PATTERN, email) is not None