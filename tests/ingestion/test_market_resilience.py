"""
Integration tests for the resilient market-data service: provider chain,
fallback, retries, stale-cache serving, and the no-fabrication guarantee.
Uses fake providers so behaviour is deterministic and network-free.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.ingestion.providers.base import (
    MarketDataProvider,
    ProviderError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    Quote,
)
from app.ingestion.providers.fmp_provider import FmpProvider
from app.ingestion.services.market_service import MarketService


class _FakePrimary(MarketDataProvider):
    name = "fake_primary"

    def __init__(self, price: float | None = 150.0) -> None:
        self._price = price
        self.calls = 0

    def fetch_quote(self, ticker: str, timeout_seconds: float = 10.0) -> Quote:
        self.calls += 1
        if self._price is None:
            raise ProviderUnavailableError("boom")
        return Quote(
            ticker=ticker.upper(),
            provider=self.name,
            price=self._price,
            quote_time=datetime.now(timezone.utc),
        )


class _FlakyThenOk(MarketDataProvider):
    """Fails once, then succeeds — exercises retry logic."""

    name = "flaky"

    def __init__(self, price: float = 151.0) -> None:
        self._price = price
        self.calls = 0

    def fetch_quote(self, ticker: str, timeout_seconds: float = 10.0) -> Quote:
        self.calls += 1
        if self.calls < 2:
            raise ProviderUnavailableError("transient")
        return Quote(
            ticker=ticker.upper(),
            provider=self.name,
            price=self._price,
            quote_time=datetime.now(timezone.utc),
        )


class _RateLimited(MarketDataProvider):
    name = "limited"

    def __init__(self) -> None:
        self.calls = 0

    def fetch_quote(self, ticker: str, timeout_seconds: float = 10.0) -> Quote:
        self.calls += 1
        raise ProviderRateLimitError("slow down")


def _settings(**overrides):
    from app.core.config import Settings

    base = {
        "market_primary_provider": "fake_primary",
        "market_fallback_providers": "",
        "market_fallback_enabled": True,
        "market_provider_timeout_seconds": 5.0,
        "market_provider_max_attempts": 2,
        "market_quote_ttl_seconds": 60,
        "market_cache_stale_seconds": 900,
        "market_cache_max_entries": 64,
        "market_cache_backend": "memory",
    }
    base.update(overrides)
    return Settings(**base)


def _patch_registry(mapping):
    """Context-manager-ish helper to swap the provider registry."""
    from app.ingestion.services import market_service as ms_module

    original = ms_module._REGISTRY.copy()
    ms_module._REGISTRY.clear()
    ms_module._REGISTRY.update(mapping)
    return original


def _restore_registry(original) -> None:
    from app.ingestion.services import market_service as ms_module

    ms_module._REGISTRY.clear()
    ms_module._REGISTRY.update(original)


def test_primary_provider_used_first() -> None:
    service = MarketService(_settings())
    original = _patch_registry({"fake_primary": _FakePrimary})
    try:
        data = service.get_market_data("AAPL")
        assert data.current_price == 150.0
        assert data.provider == "fake_primary"
        assert data.cached is False
        assert data.stale is False
    finally:
        _restore_registry(original)


def test_cache_hit_avoids_second_provider_call() -> None:
    service = MarketService(_settings())
    fake = _FakePrimary(price=150.0)
    original = _patch_registry({"fake_primary": lambda: fake})
    try:
        service.get_market_data("AAPL")
        service.get_market_data("AAPL")
        # Two calls but only one real provider fetch (second is a cache hit).
        assert fake.calls == 1
    finally:
        _restore_registry(original)


def test_fallback_engaged_when_primary_fails() -> None:
    service = MarketService(_settings(market_fallback_providers="flaky"))
    fake_primary = _FakePrimary(price=None)  # always fails
    fake_fallback = _FlakyThenOk(price=151.0)
    original = _patch_registry(
        {"fake_primary": lambda: fake_primary, "flaky": lambda: fake_fallback}
    )
    try:
        data = service.get_market_data("MSFT")
        assert data.current_price == 151.0
        assert data.provider == "flaky"
    finally:
        _restore_registry(original)


def test_stale_cache_available_after_fresh_ttl() -> None:
    service = MarketService(_settings())
    original = _patch_registry({"fake_primary": _FakePrimary})
    try:
        service.get_market_data("AAPL")
        stale = service._cache.get_stale("AAPL")
        assert stale is not None
        assert stale.price == 150.0
    finally:
        _restore_registry(original)


def test_rate_limited_primary_falls_back() -> None:
    service = MarketService(_settings(market_fallback_providers="flaky"))
    fake_fallback = _FlakyThenOk(price=151.0)
    original = _patch_registry(
        {"fake_primary": _RateLimited, "flaky": lambda: fake_fallback}
    )
    try:
        data = service.get_market_data("AAPL")
        assert data.current_price == 151.0
        assert data.provider == "flaky"
    finally:
        _restore_registry(original)


def test_total_failure_raises_without_fabrication() -> None:
    import pytest

    service = MarketService(_settings())
    original = _patch_registry({"fake_primary": lambda: _FakePrimary(price=None)})
    try:
        with pytest.raises(ProviderUnavailableError):
            service.get_market_data("ZZZZ")
    finally:
        _restore_registry(original)


class TestFmpProviderParsing:
    """Verify FMP response parsing without network access."""

    def _make(self, response):
        """Build an FmpProvider whose urlopen returns ``response``."""
        from unittest.mock import patch

        provider = FmpProvider(_settings())
        provider._api_key = "test-key"
        return provider, response

    def test_parses_list_response(self) -> None:
        from unittest.mock import MagicMock, patch
        from io import BytesIO
        import json

        aapl = {
            "symbol": "AAPL",
            "price": 178.72,
            "volume": 46507931,
            "marketCap": 2794142000000,
            "beta": 1.2,
            "eps": 6.11,
            "pe": 29.25,
            "yearHigh": 199.62,
            "yearLow": 164.08,
            "exchange": "NASDAQ",
            "timestamp": 1701808401,
        }

        raw = BytesIO(json.dumps([aapl]).encode())
        provider = FmpProvider(_settings())
        provider._api_key = "test-key"

        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=raw)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            quote = provider.fetch_quote("AAPL")

        assert quote.price == 178.72
        assert quote.provider == "fmp"
        assert quote.volume == 46507931
        assert quote.market_cap == 2794142000000
        assert quote.beta == 1.2
        assert quote.pe_ratio == 29.25
        assert quote.eps == 6.11
        assert quote.week_52_high == 199.62
        assert quote.week_52_low == 164.08
        assert quote.exchange == "NASDAQ"

    def test_missing_key_raises_unavailable(self) -> None:
        provider = FmpProvider(_settings())
        provider._api_key = ""
        try:
            provider.fetch_quote("AAPL")
        except ProviderUnavailableError:
            return
        raise AssertionError("Missing API key should raise ProviderUnavailableError")

    def test_error_message_raises_provider_error(self) -> None:
        from unittest.mock import MagicMock, patch
        from io import BytesIO
        import json

        raw = BytesIO(
            json.dumps({"Error Message": "Invalid API key"}).encode()
        )
        provider = FmpProvider(_settings())
        provider._api_key = "bad-key"

        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=raw)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            try:
                provider.fetch_quote("AAPL")
            except ProviderError as exc:
                assert "Invalid API key" in str(exc)
                return
        raise AssertionError("Error Message payload should raise ProviderError")
