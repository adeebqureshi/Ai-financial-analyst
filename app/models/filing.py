"""
filing.py

Domain model representing an SEC filing.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import Field

from app.enums.filing_type import FilingType
from app.models.base import DomainModel


class Filing(DomainModel):
    """
    Represents a single SEC filing.
    """

    ticker: str = Field(
        ...,
        description="Stock ticker",
    )

    cik: str = Field(
        ...,
        description="SEC CIK",
    )

    filing_type: FilingType

    filing_date: date

    report_period: date

    accession_number: str

    local_path: Path

    source_url: str

    parsed: bool = False

    embedded: bool = False

    checksum: str | None = None