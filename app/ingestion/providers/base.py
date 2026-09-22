from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone


_MIN_PRICE = 0.01
_MAX_PRICE = 10_000_000.0
_MAX_VOLUME = 10_000_000_000_000


@dataclass(slots=True)
class Quote:
    ticker: str
    provider: str
    price: float | None
    quote_time: datetime | None = None
    currency: str | None = None
    exchange: str | None = None
    volume: int | None = None
    market_cap: float | None = None
    beta: float | None = None
    pe_ratio: float | None = None
    eps: float | None = None
    dividend_yield: float | None = None
    week_52_high: float | None = None
    week_52_low: float | None = None
    fetched_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


def _clean_float(value: object) -> float | None:
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return number


def _clean_int(value: object) -> int | None:
    number = _clean_float(value)

    if number is None:
        return None

    return int(number)


def validate_quote(quote: Quote) -> Quote:
    price = _clean_float(quote.price)

    if price is not None and not (_MIN_PRICE <= price <= _MAX_PRICE):
        price = None

    if price is None:
        raise ProviderError(
            f"Provider '{quote.provider}' returned no valid price for "
            f"{quote.ticker}"
        )

    quote.price = price

    volume = _clean_int(quote.volume)

    if volume is not None and not (0 <= volume <= _MAX_VOLUME):
        volume = None

    quote.volume = volume

    quote.market_cap = _clean_float(quote.market_cap)

    if quote.market_cap is not None and quote.market_cap < 0:
        quote.market_cap = None

    quote.beta = _clean_float(quote.beta)
    quote.pe_ratio = _clean_float(quote.pe_ratio)

    if quote.pe_ratio is not None and quote.pe_ratio < 0:
        quote.pe_ratio = None

    quote.eps = _clean_float(quote.eps)
    quote.dividend_yield = _clean_float(quote.dividend_yield)

    if quote.dividend_yield is not None and quote.dividend_yield < 0:
        quote.dividend_yield = None

    high = _clean_float(quote.week_52_high)
    low = _clean_float(quote.week_52_low)

    if high is not None and high <= 0:
        high = None

    if low is not None and low <= 0:
        low = None

    if high is not None and low is not None and low > high:
        high, low = None, None

    quote.week_52_high = high
    quote.week_52_low = low

    if quote.currency is not None:
        quote.currency = str(quote.currency).strip().upper() or None

    return quote


class MarketDataProvider(ABC):
    name: str = "abstract"

    @abstractmethod
    def fetch_quote(
        self,
        ticker: str,
        timeout_seconds: float = 10.0,
    ) -> Quote:
        """Fetch a market quote for the given ticker."""
        raise NotImplementedError


class ProviderError(Exception):
    """Base exception for market-data provider errors."""

    pass


class ProviderRateLimitError(ProviderError):
    """Raised when a provider rate limit is exceeded."""

    pass


class ProviderUnavailableError(ProviderError):
    """Raised when a provider is unavailable."""

    pass