from __future__ import annotations
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field
class DomainModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )