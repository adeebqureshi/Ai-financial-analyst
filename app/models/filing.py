"""
filing.py

Domain model representing an SEC filing.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import Field, HttpUrl, field_validator

from app.enums.filing_type import FilingType
from app.enums.processing_status import ProcessingStatus
from app.models.base import DomainModel


class Filing(DomainModel):
    """
    Represents a single SEC filing.
    """

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Stock ticker symbol",
    )

    cik: str = Field(
        ...,
        description="SEC Central Index Key",
    )

    accession_number: str = Field(
        ...,
        description="Unique SEC accession number",
    )

    filing_type: FilingType

    filing_date: date

    report_period: date

    source_url: HttpUrl

    local_path: Path

    checksum: str | None = None

    parser_status: ProcessingStatus = ProcessingStatus.PENDING

    embedding_status: ProcessingStatus = ProcessingStatus.PENDING

    indexing_status: ProcessingStatus = ProcessingStatus.PENDING

    parser_version: str | None = None

    embedding_model: str | None = None

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        """
        Normalize ticker symbol.
        """
        return value.strip().upper()

    @field_validator("cik")
    @classmethod
    def validate_cik(cls, value: str) -> str:
        """
        Validate SEC CIK.
        """
        value = value.strip()

        if not value.isdigit():
            raise ValueError("CIK must contain only digits.")

        return value