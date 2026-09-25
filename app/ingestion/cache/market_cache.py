from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from datetime import UTC, datetime

from app.core.logging import get_logger
from app.ingestion.providers.base import Quote
from app.utils.tickers import normalize_ticker

logger = get_logger(__name__)
_KEY_PREFIX = "market:quote:v1"
class MarketQuoteCache:
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
    def _redis_client(self):
        if self._backend_mode == "memory" or self._ttl <= 0:
            return None
        if self._redis_ready:
            return self._redis
        with self._lock:
            if self._redis_ready:
                return self._redis
            try:
                import redis

                from app.infrastructure.redis_cache import build_redis_url
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
                    or datetime.now(UTC).isoformat()
                ),
            )
        except (KeyError, TypeError, ValueError):
            return None
    @staticmethod
    def _key(ticker: str) -> str:
        return f"{_KEY_PREFIX}:{normalize_ticker(ticker)}"
    def get(self, ticker: str) -> Quote | None:
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
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            raw, stored_at = entry
            age = time.monotonic() - stored_at
            if age > self._ttl:
                if self._stale <= 0 or age > self._ttl + self._stale:
                    self._entries.pop(key, None)
                return None
            self._entries.move_to_end(key)
            return self._deserialize(raw)
    def get_stale(self, ticker: str) -> Quote | None:
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
    def delete(self, ticker: str) -> None:
        """Remove a cached quote from both cache backends."""
        key = self._key(ticker)
        redis = self._redis_client()
        if redis is not None:
            try:
                redis.delete(key, f"{key}:ts")
                return
            except Exception as exc:
                logger.warning(
                    "Market quote cache delete failed (%s); degrading",
                    exc.__class__.__name__,
                )
        with self._lock:
            self._entries.pop(key, None)

    def backend_name(self) -> str:
        return "redis" if self._redis_client() is not None else "memory"
    def clear(self) -> None:
        with self._lock:
            self._entries.clear()