"""
base.py

Normalized market-data provider contract and validation rules.

Every provider returns a ``Quote`` or raises a provider exception. All
providers funnel through :func:`validate_quote` so malformed payloads, absent
prices and obviously invalid numbers are rejected *at the boundary* — they can
never silently become ``0.0`` downstream.

Error taxonomy (deterministic and observable):
    - ``ProviderRateLimitError``: the provider asked us to slow down (HTTP 429
      or an equivalent signal). Callers should back off or switch provider.
    - ``ProviderUnavailableError``: transient outage, timeout, or a
      network-level failure. Retryable.
    - ``ProviderError``: malformed/changed response or validation failure
      attributable to the provider payload. Retryable once, then fall back.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Sanity bounds for a per-share price. Values outside these ranges indicate a
# malformed payload or a currency/parsing artifact, never a real quote.
_MIN_PRICE = 0.01
_MAX_PRICE = 10_000_000.0

_MAX_VOLUME = 10_000_000_000_000


@dataclass(slots=True)
class Quote:
    """
    Normalized market quote produced by any provider.

    ``price`` is ``None`` when the provider genuinely has no price — never
    ``0.0``. Optional analytics fields (``beta``, ``pe_ratio``, ...) are
    ``None`` when the provider did not supply them.
    """

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
    """Return a finite float or ``None`` (never ``0.0`` for missing data)."""
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
    """
    Validate and sanitize a quote in place.

    Rejects obviously invalid prices (non-finite, negative, absurd magnitude)
    by setting them to ``None`` — an unavailable price is not fabricated into
    a number. Raises :class:`ProviderError` only when the provider returned a
    structurally useless payload (no price at all).
    """
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
    """
    Contract every market-data provider implements.

    Providers must honour the timeout passed to :meth:`fetch_quote` and must
    translate vendor-specific failures into the exception taxonomy above
    instead of returning placeholder data.
    """

    name: str = "abstract"

    @abstractmethod
    def fetch_quote(self, ticker: str, timeout_seconds: float = 10.0) -> Quote:
        """
        Fetch a normalized quote for ``ticker``.

        Raises:
            ProviderRateLimitError: On provider rate limiting.
            ProviderUnavailableError: On timeout / network failure.
            ProviderError: On malformed or unusable responses.
        """



class ProviderError(Exception):
    """Base class for market-data provider failures."""


class ProviderRateLimitError(ProviderError):
    """The provider is rate limiting us (HTTP 429 or equivalent)."""


class ProviderUnavailableError(ProviderError):
    """The provider is temporarily unreachable or timed out."""
