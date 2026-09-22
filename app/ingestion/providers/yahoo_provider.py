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
try:
    from yfinance.exceptions import YFRateLimitError
except Exception:
    class YFRateLimitError(Exception):
class YahooProvider(MarketDataProvider):
    name = "yahoo"
    def fetch_quote(self, ticker: str, timeout_seconds: float = 10.0) -> Quote:
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
            raise ProviderError(
                f"Yahoo Finance returned unexpected payload type for {ticker}: "
                f"{type(info).__name__}"
            )
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