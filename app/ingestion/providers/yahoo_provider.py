"""
yahoo_provider.py

Primary market-data provider backed by Yahoo Finance via ``yfinance``.

NOTE (licensing): Yahoo Finance is accessed through the unofficial
``yfinance`` library. It requires no credentials but is intended for
non-commercial/personal use and may change or throttle without notice. The
provider abstraction allows replacing it (e.g. with a commercial vendor)
without touching business logic.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.logging import get_logger
from app.ingestion.providers.base import (
    MarketDataProvider,
    ProviderError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    Quote,
    validate_quote,
)
from app.utils.tickers import normalize_ticker

logger = get_logger(__name__)

try:  # pragma: no cover - import-shape guard across yfinance versions
    from yfinance.exceptions import YFRateLimitError  # type: ignore
except Exception:  # pragma: no cover

    class YFRateLimitError(Exception):  # type: ignore[no-redef]
        """Fallback shim when yfinance does not ship the rate-limit type."""


class YahooProvider(MarketDataProvider):
    """Fetch normalized quotes from Yahoo Finance via ``yfinance``."""

    name = "yahoo"

    def fetch_quote(self, ticker: str, timeout_seconds: float = 10.0) -> Quote:
        """
        Fetch a quote for ``ticker``.

        ``yfinance`` has no first-class request timeout, so the library-level
        socket configuration is left untouched; reliability is provided by
        the service layer (retries, fallback chain, cache) rather than by
        silently degrading data quality here.
        """
        ticker = normalize_ticker(ticker)
        logger.info("Fetching market quote: provider=yahoo ticker=%s", ticker)

        try:
            import yfinance as yf

            info = yf.Ticker(ticker).info or {}
        except YFRateLimitError as exc:
            raise ProviderRateLimitError(
                f"Yahoo Finance rate limit hit for {ticker}"
            ) from exc
        except Exception as exc:
            raise ProviderUnavailableError(
                f"Yahoo Finance unavailable for {ticker}: "
                f"{exc.__class__.__name__}"
            ) from exc

        if not isinstance(info, dict):
            # Changed/malformed provider payload shape.
            raise ProviderError(
                f"Yahoo Finance returned unexpected payload type for {ticker}: "
                f"{type(info).__name__}"
            )

        # Regular market timestamps arrive as epoch seconds.
        quote_time: datetime | None = None
        raw_time = info.get("regularMarketTime")
        if isinstance(raw_time, (int, float)) and raw_time > 0:
            try:
                quote_time = datetime.fromtimestamp(raw_time, tz=timezone.utc)
            except (OverflowError, OSError, ValueError):
                quote_time = None

        quote = Quote(
            ticker=ticker,
            provider=self.name,
            price=info.get("currentPrice") or info.get("regularMarketPrice"),
            quote_time=quote_time,
            currency=info.get("currency"),
            exchange=info.get("fullExchangeName") or info.get("exchange"),
            volume=info.get("volume") or info.get("regularMarketVolume"),
            market_cap=info.get("marketCap"),
            beta=info.get("beta"),
            pe_ratio=info.get("trailingPE"),
            eps=info.get("trailingEps"),
            dividend_yield=info.get("dividendYield"),
            week_52_high=info.get("fiftyTwoWeekHigh"),
            week_52_low=info.get("fiftyTwoWeekLow"),
        )

        return validate_quote(quote)
