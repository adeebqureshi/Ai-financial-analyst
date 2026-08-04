"""
metadata.py

Metadata associated with ingested financial documents.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import Field, HttpUrl

from app.models.base import DomainModel


class Metadata(DomainModel):
    """
    Metadata describing an ingested document.
    """

    source: str = Field(
        ...,
        description="Source system (SEC, Yahoo Finance, FMP, etc.)",
    )

    source_url: HttpUrl

    checksum: str

    valid_at: datetime = Field(
        ...,
        description="When the information became valid.",
    )

    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When our system ingested the document.",
    )

    parser_version: str | None = None

    embedding_model: str | None = None

    chunk_count: int | None = Field(
        default=None,
        ge=0,
    )

    embedding_count: int | None = Field(
        default=None,
        ge=0,
    )