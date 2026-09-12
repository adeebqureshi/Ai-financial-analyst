"""
market_service.py

Resilient market-data retrieval service.

Design:
    - **Provider chain**: configuration-driven, deterministic order — the
      primary provider first, then the configured fallbacks (if enabled).
      All providers implement :class:`MarketDataProvider` and return a
      validated :class:`Quote`, so vendor failure modes are translated at
      the boundary.
    - **Retries**: transient errors are retried with exponential backoff
      (bounded); rate-limit errors back off and then move to the next
      provider.
    - **Cache**: validated quotes are stored in a TTL cache (Redis with an
      in-process fallback). On a total provider outage, a quote inside the
      stale window may be served and is flagged ``stale=True``.
    - **No fabrication**: when no provider can supply a price, the service
      raises :class:`ProviderUnavailableError` — it never returns ``0.0`` or
      a placeholder.
"""

from __future__ import annotations

import time

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.enums.exchange import Exchange
from app.ingestion.cache.market_cache import MarketQuoteCache
from app.ingestion.providers.base import (
    MarketDataProvider,
    ProviderError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from app.ingestion.providers.fmp_provider import FmpProvider
from app.ingestion.providers.yahoo_provider import YahooProvider
from app.models.market import MarketData
from app.utils.tickers import normalize_ticker

logger = get_logger(__name__)

_RATE_LIMIT_BACKOFF_SECONDS = 2.0
_MAX_BACKOFF_SECONDS = 4.0

_REGISTRY: dict[str, type[MarketDataProvider]] = {
    YahooProvider.name: YahooProvider,
    FmpProvider.name: FmpProvider,
}

# Lazy import for demo provider to avoid circular imports
_demo_provider_cls: type[MarketDataProvider] | None = None


def _get_demo_provider_cls() -> type[MarketDataProvider]:
    global _demo_provider_cls
    if _demo_provider_cls is None:
        from app.demo.providers.demo_market_provider import DemoMarketProvider

        _demo_provider_cls = DemoMarketProvider
    return _demo_provider_cls


def _register_demo_provider() -> None:
    """Register the demo provider in the global registry."""
    _REGISTRY["demo"] = _get_demo_provider_cls()


class MarketService:
    """
    Service responsible for retrieving live market data with provider
    fallback, retries, caching and explicit failure semantics.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._cache = MarketQuoteCache(
            ttl_seconds=self._settings.market_quote_ttl_seconds,
            stale_seconds=self._settings.market_cache_stale_seconds,
            max_entries=self._settings.market_cache_max_entries,
            backend=self._settings.market_cache_backend,
        )

    # ── Provider chain ────────────────────────────────────────────────────

    def _provider_chain(self) -> list[MarketDataProvider]:
        """Deterministic provider order: primary, then configured fallbacks."""
        settings = self._settings

        # In demo mode, use the demo provider exclusively
        if settings.is_demo_mode:
            _register_demo_provider()
            names: list[str] = ["demo"]
        else:
            names: list[str] = [settings.market_primary_provider.strip().lower()]

            if settings.market_fallback_enabled:
                for name in settings.market_fallback_providers.split(","):
                    name = name.strip().lower()
                    if name and name not in names:
                        names.append(name)

        providers: list[MarketDataProvider] = []
        for name in names:
            provider_cls = _REGISTRY.get(name)
            if provider_cls is None:
                logger.warning("Unknown market provider '%s' skipped", name)
                continue
            providers.append(provider_cls())
        return providers

    def _attempt_provider(
        self,
        provider: MarketDataProvider,
        ticker: str,
    ) -> MarketData:
        """Fetch from one provider with bounded retries and backoff."""
        attempts = max(int(self._settings.market_provider_max_attempts), 1)
        timeout = float(self._settings.market_provider_timeout_seconds)

        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                quote = provider.fetch_quote(ticker, timeout_seconds=timeout)
                self._cache.set(quote)
                logger.info(
                    "Market quote fetched: provider=%s ticker=%s cache=%s",
                    provider.name,
                    ticker,
                    self._cache.backend_name(),
                )
                return self._to_market_data(quote)
            except ProviderRateLimitError as exc:
                last_error = exc
                logger.warning(
                    "Provider rate limited: provider=%s ticker=%s attempt=%d/%d",
                    provider.name,
                    ticker,
                    attempt,
                    attempts,
                )
                if attempt < attempts:
                    time.sleep(min(_RATE_LIMIT_BACKOFF_SECONDS, _MAX_BACKOFF_SECONDS))
            except ProviderError as exc:
                last_error = exc
                logger.warning(
                    "Provider error: provider=%s ticker=%s attempt=%d/%d error=%s",
                    provider.name,
                    ticker,
                    attempt,
                    attempts,
                    exc,
                )
                if attempt < attempts:
                    time.sleep(min(0.5 * attempt, _MAX_BACKOFF_SECONDS))

        raise ProviderUnavailableError(
            f"Provider '{provider.name}' failed for {ticker}: {last_error}"
        ) from last_error

    # ── Public API ────────────────────────────────────────────────────────

    def get_market_data(self, ticker: str) -> MarketData:
        """
        Retrieve market data for ``ticker``.

        Deterministic order of operations (observable via logs and the
        ``provider``/``cached``/``stale`` provenance fields on the result):
            1. Fresh cache hit (within TTL) → returned with ``cached=True``.
            2. Provider chain (primary → fallbacks), each with retries.
            3. Total provider failure → stale cache hit flagged ``stale=True``
               (only within the configured stale window).
            4. Otherwise raises ``ProviderUnavailableError`` — no fabricated
               values are ever returned.

        Raises:
            ProviderUnavailableError: When no provider can supply a valid
                quote and no cached quote within the stale window exists.
        """
        ticker = normalize_ticker(ticker)
        started = time.perf_counter()

        cached = self._cache.get(ticker)
        if cached is not None:
            logger.info(
                "Market quote cache hit: provider=%s ticker=%s backend=%s",
                cached.provider,
                ticker,
                self._cache.backend_name(),
            )
            return self._to_market_data(cached, cached=True)

        providers = self._provider_chain()
        last_error: Exception | None = None

        for provider in providers:
            try:
                return self._attempt_provider(provider, ticker)
            except ProviderError as exc:
                last_error = exc
                logger.warning(
                    "Provider chain advancing: provider=%s ticker=%s reason=%s",
                    provider.name,
                    ticker,
                    exc,
                )

        stale = self._cache.get_stale(ticker)
        if stale is not None:
            logger.warning(
                "Serving stale market quote: provider=%s ticker=%s",
                stale.provider,
                ticker,
            )
            return self._to_market_data(stale, cached=True, stale=True)

        logger.warning(
            "Market data unavailable: ticker=%s duration_ms=%.0f error=%s",
            ticker,
            (time.perf_counter() - started) * 1000,
            last_error,
        )
        raise ProviderUnavailableError(
            f"No market data available for {ticker}: {last_error}"
        ) from last_error

    # ── Normalization ─────────────────────────────────────────────────────

    @staticmethod
    def _to_market_data(
        quote,
        *,
        cached: bool = False,
        stale: bool = False,
    ) -> MarketData:
        """Map a validated provider ``Quote`` to the ``MarketData`` model."""
        exchange_name = str(quote.exchange or "").upper()
        if "NYSE" in exchange_name:
            exchange = Exchange.NYSE
        elif "NASDAQ" in exchange_name:
            exchange = Exchange.NASDAQ
        else:
            exchange = Exchange.OTHER

        return MarketData(
            ticker=quote.ticker.upper(),
            exchange=exchange,
            # Quote validation guarantees a positive, finite price.
            current_price=float(quote.price),
            currency=quote.currency or "USD",
            market_cap=quote.market_cap,
            volume=quote.volume,
            beta=quote.beta,
            pe_ratio=quote.pe_ratio,
            eps=quote.eps,
            dividend_yield=quote.dividend_yield,
            week_52_high=quote.week_52_high,
            week_52_low=quote.week_52_low,
            provider=quote.provider,
            provider_time=quote.quote_time,
            cached=cached,
            stale=stale,
        )
