"""
market.py

Domain model representing live market data.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import Field

from app.enums.exchange import Exchange
from app.models.base import DomainModel


class MarketData(DomainModel):
    """
    Represents a live market snapshot for a company.
    """

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Stock ticker symbol",
    )

    exchange: Exchange

    current_price: float = Field(
        ...,
        gt=0,
        description="Current market price",
    )

    currency: str = Field(
        default="USD",
    )

    market_cap: float | None = Field(
        default=None,
        ge=0,
    )

    volume: int | None = Field(
        default=None,
        ge=0,
    )

    beta: float | None = None

    pe_ratio: float | None = Field(
        default=None,
        ge=0,
    )

    eps: float | None = None

    dividend_yield: float | None = Field(
        default=None,
        ge=0,
    )

    week_52_high: float | None = Field(
        default=None,
        ge=0,
    )

    week_52_low: float | None = Field(
        default=None,
        ge=0,
    )

    snapshot_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Time when market data was captured.",
    )