"""
Market-data quote cache.

Single caching architecture for market quotes (no second cache stack):
    - **Redis backend** (production): reuses the existing Redis infrastructure
      (``app.infrastructure.redis.build_redis_url``) with bounded socket
      timeouts; failures degrade gracefully to the in-process backend.
    - **In-process TTL backend** (development / fallback): a thread-safe,
      bounded OrderedDict (LRU eviction) — safe for concurrent requests.

Freshness model:
    - Entries within ``ttl_seconds`` are served as fresh cache hits.
    - Entries within the additional ``stale_seconds`` window are served only
      via :meth:`MarketQuoteCache.get_stale` (used when every provider fails)
      so consumers can flag the data as stale.
    - Entries older than the stale window are dropped.
"""

from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone

from app.core.logging import get_logger
from app.ingestion.providers.base import Quote
from app.utils.tickers import normalize_ticker

logger = get_logger(__name__)

_KEY_PREFIX = "market:quote:v1"


class MarketQuoteCache:
    """
    TTL cache for market quotes with Redis/in-memory backends and graceful
    degradation.

    Args:
        ttl_seconds: Freshness window for normal cache hits.
        stale_seconds: Extra window during which a stale entry may still be
            served during provider outages (0 disables stale serving).
        max_entries: Bounded size for the in-process backend (LRU eviction).
        backend: ``"auto"`` (Redis when reachable, else in-process),
            ``"redis"``, or ``"memory"``.
    """

    def __init__(
        self,
        *,
        ttl_seconds: int = 60,
        stale_seconds: int = 900,
        max_entries: int = 1024,
        backend: str = "auto",
    ) -> None:
        self._ttl = max(int(ttl_seconds), 0)
        self._stale = max(int(stale_seconds), 0)
        self._max_entries = max(int(max_entries), 1)
        self._backend_mode = backend
        self._lock = threading.Lock()
        self._entries: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self._redis = None
        self._redis_ready = False

        if self._ttl <= 0:
            logger.info("Market quote cache disabled (ttl_seconds=0)")

    # ── Redis plumbing ────────────────────────────────────────────────────

    def _redis_client(self):
        """Lazily connect to Redis once; ``None`` when unavailable."""
        if self._backend_mode == "memory" or self._ttl <= 0:
            return None
        if self._redis_ready:
            return self._redis

        with self._lock:
            if self._redis_ready:
                return self._redis
            try:
                from app.infrastructure.redis_cache import build_redis_url

                import redis

                client = redis.Redis.from_url(
                    build_redis_url(),
                    decode_responses=True,
                    socket_connect_timeout=1.0,
                    socket_timeout=1.0,
                )
                client.ping()
                self._redis = client
                logger.info("Market quote cache connected to Redis")
            except Exception as exc:
                logger.info(
                    "Market quote cache using in-process backend "
                    "(Redis unavailable: %s)",
                    exc.__class__.__name__,
                )
                self._redis = None
            finally:
                self._redis_ready = True
        return self._redis

    # ── Serialization ─────────────────────────────────────────────────────

    @staticmethod
    def _serialize(quote: Quote) -> str:
        return json.dumps(
            {
                "ticker": quote.ticker,
                "provider": quote.provider,
                "price": quote.price,
                "quote_time": quote.quote_time.isoformat()
                if quote.quote_time
                else None,
                "currency": quote.currency,
                "exchange": quote.exchange,
                "volume": quote.volume,
                "market_cap": quote.market_cap,
                "beta": quote.beta,
                "pe_ratio": quote.pe_ratio,
                "eps": quote.eps,
                "dividend_yield": quote.dividend_yield,
                "week_52_high": quote.week_52_high,
                "week_52_low": quote.week_52_low,
                "fetched_at": quote.fetched_at.isoformat(),
            }
        )

    @staticmethod
    def _deserialize(raw: str) -> Quote | None:
        try:
            data = json.loads(raw)
            return Quote(
                ticker=data["ticker"],
                provider=data["provider"],
                price=data["price"],
                quote_time=(
                    datetime.fromisoformat(data["quote_time"])
                    if data.get("quote_time")
                    else None
                ),
                currency=data.get("currency"),
                exchange=data.get("exchange"),
                volume=data.get("volume"),
                market_cap=data.get("market_cap"),
                beta=data.get("beta"),
                pe_ratio=data.get("pe_ratio"),
                eps=data.get("eps"),
                dividend_yield=data.get("dividend_yield"),
                week_52_high=data.get("week_52_high"),
                week_52_low=data.get("week_52_low"),
                fetched_at=datetime.fromisoformat(
                    data.get("fetched_at")
                    or datetime.now(timezone.utc).isoformat()
                ),
            )
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _key(ticker: str) -> str:
        return f"{_KEY_PREFIX}:{normalize_ticker(ticker)}"

    def get(self, ticker: str) -> Quote | None:
        """Return the cached quote when it is within the fresh TTL window."""
        if self._ttl <= 0:
            return None

        key = self._key(ticker)

        redis = self._redis_client()
        if redis is not None:
            try:
                raw = redis.get(key)
                if raw is None:
                    return None
                stored_at = float(redis.get(f"{key}:ts") or 0.0)
                if stored_at and (time.time() - stored_at) > self._ttl:
                    return None
                return self._deserialize(raw)
            except Exception as exc:
                logger.warning(
                    "Market quote cache read failed (%s); degrading",
                    exc.__class__.__name__,
                )
                # Fall through to the in-process backend.

        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            raw, stored_at = entry
            age = time.monotonic() - stored_at
            if age > self._ttl:
                # Only evict once the entry is too old even for stale serving,
                # so a concurrent/impending get_stale() can still use it.
                if self._stale <= 0 or age > self._ttl + self._stale:
                    self._entries.pop(key, None)
                return None
            self._entries.move_to_end(key)
            return self._deserialize(raw)

    def get_stale(self, ticker: str) -> Quote | None:
        """
        Return a cached quote beyond the fresh TTL but within the stale
        window (used only when all providers fail). ``None`` when the entry
        is too old or stale serving is disabled.
        """
        if self._ttl <= 0 or self._stale <= 0:
            return None

        key = self._key(ticker)
        max_age = self._ttl + self._stale

        redis = self._redis_client()
        if redis is not None:
            try:
                raw = redis.get(key)
                if raw is None:
                    return None
                stored_at = float(redis.get(f"{key}:ts") or 0.0)
                if stored_at and (time.time() - stored_at) > max_age:
                    return None
                return self._deserialize(raw)
            except Exception as exc:
                logger.warning(
                    "Market quote cache stale read failed (%s); degrading",
                    exc.__class__.__name__,
                )

        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            raw, stored_at = entry
            if time.monotonic() - stored_at > max_age:
                self._entries.pop(key, None)
                return None
            return self._deserialize(raw)

    def set(self, quote: Quote) -> None:
        """Store a quote (best-effort; failures never break the pipeline)."""
        if self._ttl <= 0:
            return

        key = self._key(quote.ticker)
        payload = self._serialize(quote)

        redis = self._redis_client()
        if redis is not None:
            try:
                expire = self._ttl + self._stale
                pipe = redis.pipeline()
                pipe.set(key, payload, ex=expire)
                pipe.set(f"{key}:ts", repr(time.time()), ex=expire)
                pipe.execute()
                return
            except Exception as exc:
                logger.warning(
                    "Market quote cache write failed (%s); degrading",
                    exc.__class__.__name__,
                )

        with self._lock:
            self._entries[key] = (payload, time.monotonic())
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    def backend_name(self) -> str:
        """Return the active backend name (``redis`` or ``memory``)."""
        return "redis" if self._redis_client() is not None else "memory"

    def clear(self) -> None:
        """Drop every in-process entry (Redis keys expire naturally)."""
        with self._lock:
            self._entries.clear()
