"""
company.py

Domain model representing a publicly traded company.
"""

from __future__ import annotations

from pydantic import Field, HttpUrl, field_validator

from app.enums.exchange import Exchange
from app.models.base import DomainModel


class Company(DomainModel):
    """
    Represents a publicly traded company.
    """

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Stock ticker symbol",
        examples=["AAPL"],
    )

    cik: str = Field(
        ...,
        description="SEC Central Index Key",
        examples=["320193"],
    )

    name: str = Field(
        ...,
        description="Official company name",
    )

    exchange: Exchange = Field(
        ...,
        description="Stock exchange",
    )

    sector: str = Field(
        ...,
        description="Business sector",
    )

    industry: str = Field(
        ...,
        description="Business industry",
    )

    country: str = Field(
        ...,
        description="Country of incorporation",
    )

    currency: str = Field(
        default="USD",
        description="Trading currency",
    )

    website: HttpUrl | None = Field(
        default=None,
        description="Official company website",
    )

    market_cap: float | None = Field(
        default=None,
        ge=0,
        description="Current market capitalization",
    )

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        """
        Normalize ticker symbols.
        """
        value = value.strip().upper()

        if len(value) > 10:
            raise ValueError("Ticker length cannot exceed 10 characters.")

        return value

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