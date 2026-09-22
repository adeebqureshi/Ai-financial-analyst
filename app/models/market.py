from __future__ import annotations
from datetime import datetime, timezone
from pydantic import Field
from app.enums.exchange import Exchange
from app.models.base import DomainModel
class MarketData(DomainModel):
    ticker: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Stock ticker symbol",
    )
    exchange: Exchange
    current_price: float | None = Field(
        default=None,
        ge=0,
        description=(
            "Current market price, or None when genuinely unavailable "
            "(never 0.0 as a placeholder)."
        ),
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
    provider: str | None = Field(
        default=None,
        description="Market-data provider that supplied this snapshot.",
    )
    provider_time: datetime | None = Field(
        default=None,
        description="Provider's own quote timestamp, when supplied.",
    )
    cached: bool = Field(
        default=False,
        description="True when served from the quote cache.",
    )
    stale: bool = Field(
        default=False,
        description=(
            "True when the snapshot exceeds the normal freshness TTL and is "
            "only being served because all providers failed."
        ),
    )