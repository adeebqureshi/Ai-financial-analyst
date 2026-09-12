"""
Tests for the market-data provider abstraction, validation and cache.

These exercise the boundary guarantees: fabricated / missing / malformed
provider data must never become a real-looking number downstream.
"""

from __future__ import annotations

import time

from app.ingestion.cache.market_cache import MarketQuoteCache
from app.ingestion.providers.base import (
    ProviderError,
    Quote,
    validate_quote,
)


class TestValidateQuote:
    """Boundary validation must reject bad prices and sanitize analytics."""

    def _quote(self, **overrides) -> Quote:
        data = {
            "ticker": "AAPL",
            "provider": "test",
            "price": 150.0,
        }
        data.update(overrides)
        return Quote(**data)

    def test_valid_price_passes_through(self) -> None:
        quote = validate_quote(self._quote(price=150.0))
        assert quote.price == 150.0

    def test_missing_price_raises(self) -> None:
        # The key guarantee: a missing price is NOT silently turned into 0.0.
        try:
            validate_quote(self._quote(price=None))
        except ProviderError:
            return
        raise AssertionError("Missing price should raise ProviderError")

    def test_zero_price_raises(self) -> None:
        try:
            validate_quote(self._quote(price=0.0))
        except ProviderError:
            return
        raise AssertionError("Zero price should raise ProviderError")

    def test_negative_price_raises(self) -> None:
        try:
            validate_quote(self._quote(price=-5.0))
        except ProviderError:
            return
        raise AssertionError("Negative price should raise ProviderError")

    def test_absurd_price_raises(self) -> None:
        try:
            validate_quote(self._quote(price=1e12))
        except ProviderError:
            return
        raise AssertionError("Absurd price should raise ProviderError")

    def test_nan_price_raises(self) -> None:
        try:
            validate_quote(self._quote(price=float("nan")))
        except ProviderError:
            return
        raise AssertionError("NaN price should raise ProviderError")

    def test_infinite_price_raises(self) -> None:
        try:
            validate_quote(self._quote(price=float("inf")))
        except ProviderError:
            return
        raise AssertionError("Infinite price should raise ProviderError")

    def test_malformed_range_dropped(self) -> None:
        quote = validate_quote(
            self._quote(week_52_high=100.0, week_52_low=200.0)
        )
        assert quote.week_52_high is None
        assert quote.week_52_low is None

    def test_negative_volume_dropped(self) -> None:
        quote = validate_quote(self._quote(volume=-1))
        assert quote.volume is None

    def test_currency_normalized(self) -> None:
        quote = validate_quote(self._quote(currency="  usd "))
        assert quote.currency == "USD"


class TestMarketQuoteCache:
    """TTL cache: freshness, stale window, LRU bounds and thread safety."""

    def test_miss_when_empty(self) -> None:
        cache = MarketQuoteCache(
            ttl_seconds=60, stale_seconds=900, max_entries=4, backend="memory"
        )
        assert cache.get("AAPL") is None
        assert cache.backend_name() == "memory"

    def test_set_then_get_within_ttl(self) -> None:
        cache = MarketQuoteCache(
            ttl_seconds=60, stale_seconds=900, max_entries=4, backend="memory"
        )
        quote = Quote(ticker="AAPL", provider="test", price=150.0)
        cache.set(quote)

        cached = cache.get("AAPL")
        assert cached is not None
        assert cached.price == 150.0
        assert cached.ticker == "AAPL"

    def test_expired_entry_not_returned_as_fresh(self) -> None:
        cache = MarketQuoteCache(
            ttl_seconds=0, stale_seconds=900, max_entries=4, backend="memory"
        )
        # ttl=0 disables caching entirely.
        cache.set(Quote(ticker="AAPL", provider="test", price=150.0))
        assert cache.get("AAPL") is None

    def test_stale_served_only_via_get_stale(self) -> None:
        cache = MarketQuoteCache(
            ttl_seconds=1, stale_seconds=900, max_entries=4, backend="memory"
        )
        cache.set(Quote(ticker="AAPL", provider="test", price=150.0))
        assert cache.get("AAPL") is not None

        time.sleep(1.1)
        assert cache.get("AAPL") is None
        stale = cache.get_stale("AAPL")
        assert stale is not None
        assert stale.price == 150.0

    def test_lru_eviction(self) -> None:
        cache = MarketQuoteCache(
            ttl_seconds=60, stale_seconds=900, max_entries=2, backend="memory"
        )
        for ticker in ("AAPL", "MSFT", "GOOG"):
            cache.set(Quote(ticker=ticker, provider="test", price=100.0))

        assert cache.get("AAPL") is None
        assert cache.get("MSFT") is not None
        assert cache.get("GOOG") is not None

    def test_provenance_preserved_through_round_trip(self) -> None:
        from datetime import datetime, timezone

        quote = Quote(
            ticker="AAPL",
            provider="yahoo",
            price=150.0,
            quote_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        cache = MarketQuoteCache(
            ttl_seconds=60, stale_seconds=900, max_entries=4, backend="memory"
        )
        cache.set(quote)
        cached = cache.get("AAPL")
        assert cached is not None
        assert cached.provider == "yahoo"
        assert cached.quote_time == datetime(2026, 1, 1, tzinfo=timezone.utc)

    def test_concurrent_writes_do_not_crash(self) -> None:
        import threading

        cache = MarketQuoteCache(
            ttl_seconds=60, stale_seconds=900, max_entries=64, backend="memory"
        )

        def worker(ticker: str) -> None:
            for _ in range(50):
                cache.set(Quote(ticker=ticker, provider="test", price=100.0))
                cache.get(ticker)

        threads = [
            threading.Thread(target=worker, args=(f"T{i}",)) for i in range(8)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        # Survived concurrent access without exception.
