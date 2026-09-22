from __future__ import annotations
import re
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
class UserCreate(BaseModel):
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
    model_config = ConfigDict(populate_by_name=True)
    id: str = Field(..., description="Unique user identifier.")
    email: str = Field(..., description="The user's email address.")
    is_active: bool = Field(default=True, description="Whether the account is active.")
    created_at: datetime | None = Field(
        default=None,
        description="UTC timestamp of account creation.",
    )
class Token(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    access_token: str = Field(..., description="The encoded JWT access token.")
    token_type: str = Field(default="bearer", description="Token type indicator.")
def is_valid_email(email: str) -> bool:
    return re.fullmatch(_EMAIL_PATTERN, email) is not None