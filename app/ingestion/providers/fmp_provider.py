from __future__ import annotations
import urllib.error
import urllib.request
from datetime import datetime, timezone
from json import JSONDecodeError
from app.core.constants import FMP_API_BASE_URL
from app.core.logging import get_logger
from app.core.config import Settings, get_settings
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
class FmpProvider(MarketDataProvider):
    name = "fmp"
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._api_key = self._settings.fmp_api_key_str.strip()
    def fetch_quote(self, ticker: str, timeout_seconds: float = 10.0) -> Quote:
        ticker = normalize_ticker(ticker)
        if not self._api_key:
            raise ProviderUnavailableError(
                "FMP fallback provider has no API key configured "
                "(set FMP_API_KEY)."
            )
        url = (
            f"{FMP_API_BASE_URL}/quote/{ticker}"
            f"?apikey={self._api_key}"
        )
        logger.info("Fetching market quote: provider=fmp ticker=%s", ticker)
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "ai-financial-analyst/0.1"},
            )
            with urllib.request.urlopen(request, timeout=timeout_seconds) as resp:
                import json
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                raise ProviderRateLimitError(
                    f"FMP rate limit hit for {ticker}"
                ) from exc
            raise ProviderUnavailableError(
                f"FMP HTTP {exc.code} for {ticker}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ProviderUnavailableError(
                f"FMP unavailable for {ticker}: {exc.__class__.__name__}"
            ) from exc
        except (JSONDecodeError, ValueError) as exc:
            raise ProviderError(
                f"FMP returned invalid JSON for {ticker}"
            ) from exc
        if isinstance(payload, dict) and "Error Message" in payload:
            raise ProviderError(
                f"FMP error for {ticker}: {payload['Error Message']}"
            )
        if isinstance(payload, list) and payload:
            info = payload[0]
        elif isinstance(payload, dict):
            info = payload
        else:
            raise ProviderError(
                f"FMP returned an unexpected payload for {ticker}: "
                f"{type(payload).__name__}"
            )
        if not isinstance(info, dict):
            raise ProviderError(
                f"FMP returned a non-object quote for {ticker}"
            )
        quote_time: datetime | None = None
        raw_time = info.get("timestamp")
        if isinstance(raw_time, (int, float)) and raw_time > 0:
            try:
                quote_time = datetime.fromtimestamp(raw_time, tz=timezone.utc)
            except (OverflowError, OSError, ValueError):
                quote_time = None
        result = Quote(
            ticker=info.get("symbol") or ticker,
            provider=self.name,
            price=info.get("price"),
            quote_time=quote_time,
            currency="USD",
            exchange=info.get("exchange"),
            volume=info.get("volume"),
            market_cap=info.get("marketCap"),
            beta=info.get("beta"),
            pe_ratio=info.get("pe"),
            eps=info.get("eps"),
            dividend_yield=info.get("dividendYield"),
            week_52_high=info.get("yearHigh"),
            week_52_low=info.get("yearLow"),
        )
        return validate_quote(result)