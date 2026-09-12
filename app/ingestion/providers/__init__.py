"""
Provider abstraction for live market data.

This package decouples the application from any single market-data vendor.
The Yahoo Finance provider (``yfinance``) is the default primary provider;
Financial Modeling Prep (FMP) is the lightweight fallback. Providers are selected
and chained via configuration (see ``Settings.market_*``).

NOTE (licensing): Yahoo Finance's public API is unofficial and intended for
non-commercial/personal use. FMP has a free tier and paid plans.
FMP requires an API key; both are swappable without touching
business logic because all consumers depend on ``MarketDataProvider`` and the
normalized ``Quote`` model defined here.
"""

from __future__ import annotations

from app.ingestion.providers.base import (
    MarketDataProvider,
    ProviderError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    Quote,
    validate_quote,
)
from app.ingestion.providers.fmp_provider import FmpProvider
from app.ingestion.providers.yahoo_provider import YahooProvider

__all__ = [
    "MarketDataProvider",
    "ProviderError",
    "ProviderRateLimitError",
    "ProviderUnavailableError",
    "Quote",
    "FmpProvider",
    "YahooProvider",
    "validate_quote",
]
