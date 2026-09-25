from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

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
            quote_time=datetime.now(UTC),
        )
class _FlakyThenOk(MarketDataProvider):
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
            quote_time=datetime.now(UTC),
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
        assert fake.calls == 1
    finally:
        _restore_registry(original)
def test_fallback_engaged_when_primary_fails() -> None:
    service = MarketService(_settings(market_fallback_providers="flaky"))
    fake_primary = _FakePrimary(price=None)
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
def test_demo_mode_false_cannot_import_or_select_demo_provider() -> None:
    import builtins

    import pytest

    from app.ingestion.services import market_service as ms_module

    real_import = builtins.__import__
    demo_imports: list[str] = []

    def tracking_import(name, *args, **kwargs):
        if "demo_market_provider" in name:
            demo_imports.append(name)
        return real_import(name, *args, **kwargs)

    settings = _settings(
        demo_mode=False,
        market_primary_provider="demo",
        market_fallback_providers="demo",
    )
    original = _patch_registry({"demo": _FakePrimary})
    try:
        with patch(
            "builtins.__import__", side_effect=tracking_import
        ):
            with pytest.raises(ProviderUnavailableError, match="No market providers"):
                MarketService(settings)._provider_chain()
            with pytest.raises(RuntimeError, match="DEMO_MODE=true"):
                ms_module._get_demo_provider_cls(settings)
            with pytest.raises(RuntimeError, match="DEMO_MODE=true"):
                ms_module._register_demo_provider(settings)
        assert "demo" not in demo_imports
    finally:
        _restore_registry(original)


def test_demo_mode_false_uses_real_provider() -> None:
    service = MarketService(_settings(demo_mode=False))
    original = _patch_registry({"fake_primary": _FakePrimary})
    try:
        data = service.get_market_data("AAPL")
        assert data.provider == "fake_primary"
    finally:
        _restore_registry(original)


def test_demo_mode_false_real_failure_has_no_demo_fallback() -> None:
    import pytest

    from app.ingestion.services import market_service as ms_module

    service = MarketService(
        _settings(
            demo_mode=False,
            market_fallback_providers="demo",
            market_provider_max_attempts=1,
        )
    )
    original_registry = _patch_registry(
        {"fake_primary": lambda: _FakePrimary(price=None)}
    )
    original_demo_registry = ms_module._REGISTRY.get("demo")
    try:
        with pytest.raises(ProviderUnavailableError):
            service.get_market_data("ZZZZ")
        assert "demo" not in ms_module._REGISTRY
    finally:
        if original_demo_registry is not None:
            ms_module._REGISTRY["demo"] = original_demo_registry
        _restore_registry(original_registry)


def test_demo_mode_true_uses_explicit_demo_provider() -> None:
    settings = _settings(demo_mode=True, environment="test")
    service = MarketService(settings)
    try:
        providers = service._provider_chain()
        assert [provider.name for provider in providers] == ["demo"]
    finally:
        from app.ingestion.services import market_service as ms_module

        ms_module._REGISTRY.pop("demo", None)



class TestProductionDataSourceEnforcement:
    """Issue #5: production mode must never serve demo/mock/sample data."""

    def test_production_mode_uses_only_real_providers(self) -> None:
        service = MarketService(_settings(demo_mode=False))
        original = _patch_registry(
            {"fake_primary": _FakePrimary, "demo": _FakePrimary}
        )
        try:
            names = [provider.name for provider in service._provider_chain()]
            assert "demo" not in names
            data = service.get_market_data("AAPL")
            assert data.provider == "fake_primary"
        finally:
            _restore_registry(original)

    def test_real_provider_failure_never_falls_back_to_demo(self) -> None:
        import pytest

        service = MarketService(
            _settings(
                demo_mode=False,
                market_fallback_providers="demo",
                market_provider_max_attempts=1,
            )
        )
        original = _patch_registry(
            {"fake_primary": lambda: _FakePrimary(price=None), "demo": _FakePrimary}
        )
        try:
            with pytest.raises(ProviderUnavailableError):
                service.get_market_data("ZZZZ")
        finally:
            _restore_registry(original)

    def test_cached_demo_quote_is_rejected_in_production(self) -> None:
        service = MarketService(_settings(demo_mode=False))
        original = _patch_registry({"fake_primary": _FakePrimary})
        try:
            service._cache.set(
                Quote(
                    ticker="AAPL",
                    provider="demo",
                    price=1.0,
                    quote_time=datetime.now(UTC),
                )
            )
            data = service.get_market_data("AAPL")
            assert data.provider == "fake_primary"
            assert data.current_price == 150.0
        finally:
            _restore_registry(original)

    def test_stale_demo_quote_is_rejected_in_production(self) -> None:
        import pytest

        service = MarketService(
            _settings(demo_mode=False, market_provider_max_attempts=1)
        )
        original = _patch_registry(
            {"fake_primary": lambda: _FakePrimary(price=None)}
        )
        try:
            service._cache.set(
                Quote(
                    ticker="ZZZZ",
                    provider="demo",
                    price=1.0,
                    quote_time=datetime.now(UTC),
                )
            )
            with pytest.raises(ProviderUnavailableError):
                service.get_market_data("ZZZZ")
        finally:
            _restore_registry(original)

    def test_demo_mode_serves_demo_data_through_explicit_path(self) -> None:
        service = MarketService(_settings(demo_mode=True, environment="test"))
        try:
            providers = service._provider_chain()
            assert [provider.name for provider in providers] == ["demo"]
            data = service.get_market_data("AAPL")
            assert data.provider == "demo"
        finally:
            from app.ingestion.services import market_service as ms_module

            ms_module._REGISTRY.pop("demo", None)
            service._cache.clear()


class TestFmpProviderParsing:
    def _make(self, response):
        provider = FmpProvider(_settings())
        provider._api_key = "test-key"
        return provider, response
    def test_parses_list_response(self) -> None:
        import json
        from io import BytesIO
        from unittest.mock import MagicMock, patch
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
        import json
        from io import BytesIO
        from unittest.mock import MagicMock, patch
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