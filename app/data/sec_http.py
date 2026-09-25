"""Centralized outbound HTTP gateway for U.S. SEC requests.

Architecture (single choke point)::

    application code (SECClient / SECDownloader / SECLoader / EdgarClient)
        |
        v
    SECRequestGateway            <- the one approved SEC request API
        |
        v
    RedisStrictRateLimiter       <- distributed, atomic, shared Redis state
        |
        v
    SECHttpTransport             <- the only module allowed to call `requests`
        |
        v
    www.sec.gov / data.sec.gov

Invariants enforced by this module:

* Every outbound SEC request is admitted by one Redis-backed limiter that is
  shared by all processes, workers, threads and containers (single Redis key).
* The admission decision is a strict rolling 1-second window: at most
  ``SEC_MAX_REQUESTS_PER_SECOND`` (10) admissions in any rolling second.
* The decision is made inside a single atomic Lua script that uses Redis
  server time, so client clock skew cannot weaken the limit.
* Every retry is a new outbound request and therefore re-enters the limiter.
* If Redis is unavailable the request is *not* sent (fail closed). There is no
  direct-HTTP fallback anywhere in this module.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final
from urllib.parse import urlsplit

import requests

from app.core.constants import (
    API_MAX_RETRIES,
    API_RETRY_BACKOFF,
    API_RETRY_STATUS_CODES,
)

logger = logging.getLogger(__name__)

# ── SEC host allow-list ──────────────────────────────────────────────────────

SEC_HOSTS: Final[frozenset[str]] = frozenset(
    {
        "sec.gov",
        "www.sec.gov",
        "data.sec.gov",
        "efts.sec.gov",
        "www.efts.sec.gov",
    }
)

# ── Limiter + transport configuration ───────────────────────────────────────

SEC_MAX_REQUESTS_PER_SECOND: Final[int] = 10
SEC_RATE_LIMIT_WINDOW_SECONDS: Final[float] = 1.0
SEC_RATE_LIMIT_REDIS_KEY: Final[str] = "sec:edgar:rate_limit:rolling_window"
SEC_RATE_LIMIT_KEY_TTL_SECONDS: Final[float] = 5.0
SEC_DEFAULT_REDIS_URL: Final[str] = "redis://localhost:6379/0"

SEC_REQUEST_TIMEOUT_SECONDS: Final[float] = 30.0

SEC_MAX_ATTEMPTS: Final[int] = API_MAX_RETRIES
SEC_RETRY_BACKOFF_SECONDS: Final[float] = API_RETRY_BACKOFF
SEC_RETRY_STATUS_CODES: Final[tuple[int, ...]] = API_RETRY_STATUS_CODES


class SECRateLimitUnavailableError(RuntimeError):
    """Raised when the distributed SEC rate limiter cannot make a decision.

    This is a *fail closed* error: the caller must not send the SEC request.
    """


class SECRequestNotAllowedError(ValueError):
    """Raised when a caller tries to send a request to a non-SEC host."""


class SECRequestFailedError(RuntimeError):
    """Raised when a SEC request could not be completed after all attempts."""


def is_sec_url(url: str) -> bool:
    """Return True when ``url`` points at an official SEC host."""
    try:
        host = urlsplit(url).hostname or ""
    except ValueError:
        return False

    host = host.lower().rstrip(".")
    if not host:
        return False

    if host in SEC_HOSTS:
        return True

    return any(host.endswith(f".{sec_host}") for sec_host in SEC_HOSTS)


def ensure_sec_url(url: str) -> str:
    """Validate that ``url`` targets the SEC, returning it unchanged.

    Raises:
        SECRequestNotAllowedError: when the URL is not an SEC endpoint.
    """
    if not isinstance(url, str) or not url:
        raise SECRequestNotAllowedError("A SEC request URL is required.")

    if not is_sec_url(url):
        raise SECRequestNotAllowedError(
            f"Refusing to send a non-SEC request through the SEC gateway: {url!r}"
        )

    return url


def resolve_redis_url(explicit: str | None = None) -> str:
    """Resolve the Redis URL used by the *single* SEC rate-limit state.

    Resolution order:
        1. explicit argument
        2. ``SEC_RATE_LIMIT_REDIS_URL`` environment variable
        3. ``RATE_LIMIT_REDIS_URL`` environment variable
        4. ``REDIS_URL`` environment variable
        5. ``settings.rate_limit_redis_url``
        6. ``redis://localhost:6379/0``
    """
    for candidate in (
        explicit,
        os.getenv("SEC_RATE_LIMIT_REDIS_URL"),
        os.getenv("RATE_LIMIT_REDIS_URL"),
        os.getenv("REDIS_URL"),
    ):
        if candidate and candidate.strip():
            return candidate.strip()

    try:
        from app.core.config import get_settings

        configured = get_settings().rate_limit_redis_url
        if configured and configured.strip():
            return configured.strip()
    except Exception:  # pragma: no cover - settings are optional here
        logger.debug("Falling back to the default SEC rate-limit Redis URL.")

    return SEC_DEFAULT_REDIS_URL


class SECIdentityError(ValueError):
    """Raised when a complete SEC identifying User-Agent is unavailable."""


def _validate_user_agent(identity: str | None) -> str:
    """Validate an SEC identity as ``application/company name contact``."""
    value = (identity or "").strip()
    if not value or any(character in value for character in "\r\n"):
        raise SECIdentityError(
            "EDGAR_IDENTITY is required in the form 'Application/Company contact@example.com'."
        )

    match = re.match(
        r"^[A-Za-z][A-Za-z0-9 ._&'/-]*?\s+"
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
        value,
    )
    if match is None or "example.com" in value.lower():
        raise SECIdentityError(
            "EDGAR_IDENTITY must include an application/company identity and "
            "a non-placeholder email contact."
        )
    return value


def resolve_user_agent(explicit: str | None = None) -> str:
    """Resolve and strictly validate the gateway-owned SEC User-Agent."""
    candidate = explicit
    if candidate is None:
        try:
            from app.core.config import get_settings

            candidate = get_settings().edgar_identity
        except Exception as exc:
            raise SECIdentityError("A valid EDGAR_IDENTITY is required.") from exc
    return _validate_user_agent(candidate)


@dataclass(frozen=True, slots=True)
class SECRateLimitGrant:
    """Result of an admission decision made by the distributed limiter."""

    allowed: bool
    wait_seconds: float
    admitted_at: float
    in_window: int


# ── Distributed strict rolling-window limiter ────────────────────────────────

# Single atomic decision:
#   1. read Redis server time (shared clock for every worker/container)
#   2. drop every admission outside the rolling window
#   3. count the admissions that are still inside the window
#   4. reject when the window is already full (return the exact retry delay)
#   5. otherwise record the new admission and refresh the key TTL
#
# Everything happens in one script evaluation, so concurrent workers can never
# interleave a check with a write ("check + write" race) and can never exceed
# the window limit.
_STRICT_ROLLING_WINDOW_SCRIPT = """
local window_key = KEYS[1]
local sequence_key = KEYS[2]

local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local ttl_ms = tonumber(ARGV[3])

-- Redis server time: identical for every application process.
local redis_time = redis.call('TIME')
local now = tonumber(redis_time[1]) + (tonumber(redis_time[2]) / 1000000)

-- Admitting a request at `now` must never push the count above `limit` for
-- the closed window [now - window, now].
local window_start = now - window

redis.call('ZREMRANGEBYSCORE', window_key, '-inf', '(' .. string.format('%.6f', window_start))

local admitted = redis.call('ZCARD', window_key)

if admitted >= limit then
    local oldest = redis.call('ZRANGE', window_key, 0, 0, 'WITHSCORES')
    local wait = window
    if oldest[1] ~= nil and oldest[2] ~= nil then
        wait = (tonumber(oldest[2]) + window) - now
    end
    if wait <= 0 then
        wait = 0.001
    end
    redis.call('PEXPIRE', window_key, ttl_ms)
    return {0, string.format('%.6f', wait), '0', admitted}
end

local sequence = redis.call('INCR', sequence_key)
local member = string.format('%.6f', now) .. ':' .. tostring(sequence)

redis.call('ZADD', window_key, string.format('%.6f', now), member)
redis.call('PEXPIRE', window_key, ttl_ms)
redis.call('PEXPIRE', sequence_key, ttl_ms)

return {1, '0', string.format('%.6f', now), admitted + 1}
"""


class RedisStrictRateLimiter:
    """Strict distributed rolling-window limiter shared through Redis.

    Semantics: at most :attr:`limit` admissions inside *any* rolling
    ``window_seconds`` interval. This is deliberately **not** a token bucket -
    a token bucket of capacity 10 refilling at 10/s permits bursts and can
    admit more than 10 requests inside one second.

    All instances that share :attr:`key` share the same distributed state, so
    separate client objects, threads, workers and containers are coordinated.
    """

    LIMIT: Final[int] = SEC_MAX_REQUESTS_PER_SECOND
    WINDOW_SECONDS: Final[float] = SEC_RATE_LIMIT_WINDOW_SECONDS
    KEY: Final[str] = SEC_RATE_LIMIT_REDIS_KEY
    KEY_TTL_SECONDS: Final[float] = SEC_RATE_LIMIT_KEY_TTL_SECONDS
    DEFAULT_REDIS_URL: Final[str] = SEC_DEFAULT_REDIS_URL

    # Backwards-compatible aliases for the retired token-bucket implementation.
    CAPACITY: Final[int] = SEC_MAX_REQUESTS_PER_SECOND
    REFILL_RATE: Final[float] = SEC_MAX_REQUESTS_PER_SECOND / SEC_RATE_LIMIT_WINDOW_SECONDS
    DEFAULT_KEY: Final[str] = SEC_RATE_LIMIT_REDIS_KEY

    _RECONNECT_COOLDOWN_SECONDS: Final[float] = 5.0

    def __init__(
        self,
        redis_url: str | None = None,
        key: str = SEC_RATE_LIMIT_REDIS_KEY,
        limit: int = SEC_MAX_REQUESTS_PER_SECOND,
        window_seconds: float = SEC_RATE_LIMIT_WINDOW_SECONDS,
        key_ttl_seconds: float = SEC_RATE_LIMIT_KEY_TTL_SECONDS,
        client: Any | None = None,
    ) -> None:
        if limit < 1:
            raise ValueError("SEC rate limiter limit must be >= 1.")
        if window_seconds <= 0:
            raise ValueError("SEC rate limiter window must be > 0 seconds.")

        self._limit = int(limit)
        self._window_seconds = float(window_seconds)
        self._key = key
        self._sequence_key = f"{key}:seq"
        self._ttl_ms = max(
            1000,
            int(round(max(float(key_ttl_seconds), float(window_seconds) + 1.0) * 1000)),
        )
        self._script_sha: str | None = None
        self._lock = threading.Lock()
        self._last_connect_attempt = 0.0
        self._redis_url = resolve_redis_url(redis_url) if client is None else redis_url

        if client is not None:
            # Injected client (tests / dependency injection) - no connection.
            self._client: Any | None = client
        else:
            self._client = self._connect()

        logger.info(
            "SEC strict rate limiter ready (limit=%d per %ss, key=%s)",
            self._limit,
            self._window_seconds,
            self._key,
        )

    # ── connection handling ──────────────────────────────────────────────

    def _connect(self) -> Any:
        self._last_connect_attempt = time.monotonic()

        try:
            import redis
        except ImportError as exc:  # pragma: no cover - dependency is declared
            raise SECRateLimitUnavailableError(
                "The 'redis' package is required for SEC rate limiting."
            ) from exc

        client = redis.from_url(
            self._redis_url or SEC_DEFAULT_REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            health_check_interval=30,
        )

        # Fail closed: without Redis we cannot prove the SEC limit holds.
        try:
            client.ping()
        except Exception as exc:
            logger.error("SEC rate limiter cannot reach Redis: %s", exc)
            raise SECRateLimitUnavailableError(
                "Redis is required for SEC rate limiting but is unavailable."
            ) from exc

        return client

    def _require_client(self) -> Any:
        if self._client is not None:
            return self._client

        if time.monotonic() - self._last_connect_attempt < self._RECONNECT_COOLDOWN_SECONDS:
            raise SECRateLimitUnavailableError("SEC rate limiter Redis connection is unavailable.")

        with self._lock:
            if self._client is None:
                self._client = self._connect()

        return self._client

    def _drop_client(self) -> None:
        self._client = None
        self._last_connect_attempt = time.monotonic()

    # ── shared state description ─────────────────────────────────────────

    @property
    def key(self) -> str:
        """The shared Redis key holding the rolling window."""
        return self._key

    @property
    def sequence_key(self) -> str:
        """The shared Redis key used to keep admission members unique."""
        return self._sequence_key

    @property
    def limit(self) -> int:
        return self._limit

    @property
    def window_seconds(self) -> float:
        return self._window_seconds

    # ── admission ────────────────────────────────────────────────────────

    def _evaluate(self) -> SECRateLimitGrant:
        client = self._require_client()
        arguments = (self._limit, self._window_seconds, self._ttl_ms)

        try:
            if self._script_sha is None:
                self._script_sha = client.script_load(_STRICT_ROLLING_WINDOW_SCRIPT)

            result = client.evalsha(
                self._script_sha,
                2,
                self._key,
                self._sequence_key,
                *arguments,
            )
        except Exception as exc:
            if _is_noscript_error(exc):
                try:
                    self._script_sha = None
                    result = client.eval(
                        _STRICT_ROLLING_WINDOW_SCRIPT,
                        2,
                        self._key,
                        self._sequence_key,
                        *arguments,
                    )
                except Exception as retry_exc:
                    self._drop_client()
                    raise SECRateLimitUnavailableError(
                        "SEC rate limiter failed; the SEC request was not sent."
                    ) from retry_exc
            else:
                self._drop_client()
                raise SECRateLimitUnavailableError(
                    "SEC rate limiter failed; the SEC request was not sent."
                ) from exc

        grant = _parse_grant(result)
        if grant is None:
            raise SECRateLimitUnavailableError(
                "SEC rate limiter returned an invalid response; the SEC request was not sent."
            )

        return grant

    def check(self) -> SECRateLimitGrant:
        """Atomically decide whether one SEC request may be admitted now.

        When admitted, the admission is already recorded in the shared rolling
        window before this method returns, so the caller must send the request
        immediately. When rejected, ``wait_seconds`` is the exact time the
        caller must wait before trying again.
        """
        return self._evaluate()

    def acquire(self, max_wait_seconds: float | None = None) -> SECRateLimitGrant:
        """Block until one SEC request slot is admitted.

        Args:
            max_wait_seconds: optional cap on the total blocking time.

        Raises:
            SECRateLimitUnavailableError: when Redis cannot make a decision
                (fail closed - the caller must not send the request).
            TimeoutError: when ``max_wait_seconds`` is exceeded.
        """
        deadline = time.monotonic() + max_wait_seconds if max_wait_seconds is not None else None

        while True:
            grant = self._evaluate()
            if grant.allowed:
                return grant

            wait_seconds = max(grant.wait_seconds, 0.001)
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Timed out waiting for a SEC request slot.")
                wait_seconds = min(wait_seconds, remaining)

            time.sleep(wait_seconds)

    async def acquire_async(
        self,
        max_wait_seconds: float | None = None,
    ) -> SECRateLimitGrant:
        """Async twin of :meth:`acquire`.

        Uses the same Redis key and the same atomic script, so async and sync
        callers share one distributed limit.
        """
        deadline = time.monotonic() + max_wait_seconds if max_wait_seconds is not None else None

        while True:
            grant = await asyncio.to_thread(self._evaluate)
            if grant.allowed:
                return grant

            wait_seconds = max(grant.wait_seconds, 0.001)
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Timed out waiting for a SEC request slot.")
                wait_seconds = min(wait_seconds, remaining)

            await asyncio.sleep(wait_seconds)

    def close(self) -> None:
        """Release the Redis connection held by this limiter instance."""
        client, self._client = self._client, None
        if client is None:
            return
        try:
            client.close()
        except Exception:  # pragma: no cover - best effort cleanup
            logger.debug("Ignoring error while closing the SEC rate limiter.")


# The canonical alias used across the repository. It is the same class using
# the same Redis key, so there is exactly one distributed coordination
# mechanism for SEC traffic.
SECRateLimiter = RedisStrictRateLimiter


def _is_noscript_error(exc: Exception) -> bool:
    return "NOSCRIPT" in str(exc).upper()


def _parse_grant(result: Any) -> SECRateLimitGrant | None:
    try:
        allowed_raw, wait_raw, admitted_at_raw, in_window_raw = result[0:4]
        return SECRateLimitGrant(
            allowed=int(allowed_raw) == 1,
            wait_seconds=float(wait_raw),
            admitted_at=float(admitted_at_raw),
            in_window=int(in_window_raw),
        )
    except Exception:
        logger.error("Unexpected SEC rate limiter response: %r", result)
        return None


# ── The only HTTP transport allowed to talk to the SEC ───────────────────────


class SECHttpTransport:
    """Low-level HTTP transport for SEC endpoints.

    This class is the single place in the application that may call the
    ``requests`` transport for an SEC endpoint. It also owns the authoritative
    SEC headers (identification User-Agent, compression, accept) so every SEC
    request is identified consistently.
    """

    def __init__(
        self,
        session: requests.Session | None = None,
        user_agent: str | None = None,
        timeout: float = SEC_REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self._session = session if session is not None else requests.Session()
        self._owns_session = session is None
        self._user_agent = resolve_user_agent(user_agent)
        self._timeout = float(timeout)

    @property
    def session(self) -> requests.Session:
        return self._session

    @property
    def user_agent(self) -> str:
        return self._user_agent

    def _build_headers(self, headers: Mapping[str, str] | None) -> dict[str, str]:
        merged: dict[str, str] = {
            "User-Agent": self._user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
        }
        if headers:
            merged.update(
                {
                    str(name): str(value)
                    for name, value in headers.items()
                    if value is not None and str(name).lower() != "user-agent"
                }
            )
        # The gateway-owned identity is authoritative regardless of header casing.
        merged["User-Agent"] = self._user_agent
        return merged

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        data: Any = None,
        json_body: Any = None,
        timeout: float | None = None,
    ) -> requests.Response:
        """Perform exactly one HTTP request to the SEC."""
        return self._session.request(
            method=method.upper(),
            url=url,
            params=params,
            headers=self._build_headers(headers),
            data=data,
            json=json_body,
            timeout=self._timeout if timeout is None else float(timeout),
            allow_redirects=True,
        )

    def close(self) -> None:
        if self._owns_session:
            try:
                self._session.close()
            except Exception:  # pragma: no cover - best effort cleanup
                logger.debug("Ignoring error while closing the SEC HTTP session.")


# ── The central SEC request gateway ─────────────────────────────────────────


class SECRequestGateway:
    """Central SEC request API used by every SEC client in the repository.

    The gateway validates the target host, acquires a distributed admission
    slot for **every** outbound attempt (initial request *and* every retry),
    and only then delegates to :class:`SECHttpTransport`.
    """

    def __init__(
        self,
        limiter: Any | None = None,
        transport: Any | None = None,
        max_attempts: int = SEC_MAX_ATTEMPTS,
        backoff_seconds: float = SEC_RETRY_BACKOFF_SECONDS,
        retry_status_codes: tuple[int, ...] = SEC_RETRY_STATUS_CODES,
    ) -> None:
        self._limiter = limiter if limiter is not None else RedisStrictRateLimiter()
        self._transport = transport if transport is not None else SECHttpTransport()
        self._max_attempts = max(1, int(max_attempts))
        self._backoff_seconds = max(0.0, float(backoff_seconds))
        self._retry_status_codes = frozenset(int(code) for code in retry_status_codes)

    @property
    def limiter(self) -> Any:
        """The distributed limiter guarding every SEC request."""
        return self._limiter

    @property
    def transport(self) -> Any:
        """The HTTP transport that performs the actual SEC request."""
        return self._transport

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        data: Any = None,
        json_body: Any = None,
        timeout: float | None = None,
        max_attempts: int | None = None,
        require_sec_host: bool = True,
    ) -> requests.Response:
        """Send a request to the SEC, rate limited and retried safely."""
        if require_sec_host:
            ensure_sec_url(url)

        attempts = self._max_attempts if max_attempts is None else max(1, int(max_attempts))
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            # A retry is a NEW outbound SEC request, so it must acquire a new
            # admission slot from the same distributed limiter.
            self._limiter.acquire()

            try:
                response = self._transport.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    data=data,
                    json_body=json_body,
                    timeout=timeout,
                )
            except requests.RequestException as exc:
                last_error = exc
                logger.warning(
                    "SEC request failed (attempt %d/%d): %s",
                    attempt,
                    attempts,
                    exc,
                )
                if attempt >= attempts:
                    break
                self._sleep_before_retry(attempt)
                continue

            if response.status_code in self._retry_status_codes and attempt < attempts:
                logger.warning(
                    "SEC request returned %d (attempt %d/%d); retrying through the limiter",
                    response.status_code,
                    attempt,
                    attempts,
                )
                response.close()
                self._sleep_before_retry(attempt)
                continue

            return response

        raise SECRequestFailedError(
            f"SEC request to {url} failed after {attempts} attempt(s)."
        ) from last_error

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """Rate-limited ``GET`` against the SEC."""
        return self.request("GET", url, **kwargs)

    def get_text(self, url: str, **kwargs: Any) -> str:
        """Rate-limited ``GET`` returning the response body as text."""
        response = self.get(url, **kwargs)
        response.raise_for_status()
        return response.text

    def get_json(self, url: str, **kwargs: Any) -> Any:
        """Rate-limited ``GET`` returning the decoded JSON payload."""
        response = self.get(url, **kwargs)
        response.raise_for_status()
        return response.json()

    # ── async API (shares the exact same distributed limit) ──────────────

    async def arequest(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        data: Any = None,
        json_body: Any = None,
        timeout: float | None = None,
        max_attempts: int | None = None,
        require_sec_host: bool = True,
    ) -> requests.Response:
        """Async twin of :meth:`request`.

        The admission decision is taken with ``await limiter.acquire_async()``
        against the same Redis key, and the blocking HTTP call is offloaded to
        a worker thread, so async and sync callers cannot exceed the shared
        SEC limit together.
        """
        if require_sec_host:
            ensure_sec_url(url)

        attempts = self._max_attempts if max_attempts is None else max(1, int(max_attempts))
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            acquire_async = getattr(self._limiter, "acquire_async", None)
            if callable(acquire_async):
                await acquire_async()
            else:  # pragma: no cover - custom limiters may only be sync
                await asyncio.to_thread(self._limiter.acquire)

            try:
                response = await asyncio.to_thread(
                    self._transport.request,
                    method,
                    url,
                    params=params,
                    headers=headers,
                    data=data,
                    json_body=json_body,
                    timeout=timeout,
                )
            except requests.RequestException as exc:
                last_error = exc
                logger.warning(
                    "SEC request failed (attempt %d/%d): %s",
                    attempt,
                    attempts,
                    exc,
                )
                if attempt >= attempts:
                    break
                await asyncio.sleep(self._retry_delay(attempt))
                continue

            if response.status_code in self._retry_status_codes and attempt < attempts:
                logger.warning(
                    "SEC request returned %d (attempt %d/%d); retrying through the limiter",
                    response.status_code,
                    attempt,
                    attempts,
                )
                response.close()
                await asyncio.sleep(self._retry_delay(attempt))
                continue

            return response

        raise SECRequestFailedError(
            f"SEC request to {url} failed after {attempts} attempt(s)."
        ) from last_error

    async def aget(self, url: str, **kwargs: Any) -> requests.Response:
        """Async rate-limited ``GET`` against the SEC."""
        return await self.arequest("GET", url, **kwargs)

    async def aget_text(self, url: str, **kwargs: Any) -> str:
        """Async rate-limited ``GET`` returning the response body as text."""
        response = await self.aget(url, **kwargs)
        response.raise_for_status()
        return response.text

    async def aget_json(self, url: str, **kwargs: Any) -> Any:
        """Async rate-limited ``GET`` returning the decoded JSON payload."""
        response = await self.aget(url, **kwargs)
        response.raise_for_status()
        return response.json()

    def _sleep_before_retry(self, attempt: int) -> None:
        delay = self._retry_delay(attempt)
        if delay <= 0:
            return
        logger.info("Waiting %.2fs before the next SEC attempt.", delay)
        time.sleep(delay)

    def _retry_delay(self, attempt: int) -> float:
        if self._backoff_seconds <= 0:
            return 0.0
        return min(self._backoff_seconds * (2 ** (attempt - 1)), 8.0)

    def close(self) -> None:
        close = getattr(self._transport, "close", None)
        if callable(close):
            close()


# ── Process-wide singletons ─────────────────────────────────────────────────

_limiter_lock = threading.Lock()
_gateway_lock = threading.Lock()
_shared_limiter: RedisStrictRateLimiter | None = None
_shared_gateway: SECRequestGateway | None = None


def get_sec_rate_limiter() -> RedisStrictRateLimiter:
    """Return the process-wide distributed SEC limiter.

    Raises:
        SECRateLimitUnavailableError: when Redis is unavailable (fail closed).
    """
    global _shared_limiter
    if _shared_limiter is None:
        with _limiter_lock:
            if _shared_limiter is None:
                _shared_limiter = RedisStrictRateLimiter()
    return _shared_limiter


def set_sec_rate_limiter(limiter: RedisStrictRateLimiter | None) -> None:
    """Replace the process-wide limiter (dependency injection / tests)."""
    global _shared_limiter
    _shared_limiter = limiter


def get_sec_gateway() -> SECRequestGateway:
    """Return the process-wide SEC gateway.

    Raises:
        SECRateLimitUnavailableError: when Redis is unavailable (fail closed).
    """
    global _shared_gateway
    if _shared_gateway is None:
        with _gateway_lock:
            if _shared_gateway is None:
                _shared_gateway = SECRequestGateway(limiter=get_sec_rate_limiter())
    return _shared_gateway


def set_sec_gateway(gateway: SECRequestGateway | None) -> None:
    """Replace the process-wide gateway (dependency injection / tests)."""
    global _shared_gateway
    _shared_gateway = gateway


def reset_sec_gateway() -> None:
    """Drop the cached gateway/limiter so the next call rebuilds them."""
    global _shared_gateway, _shared_limiter
    gateway, limiter = _shared_gateway, _shared_limiter
    _shared_gateway, _shared_limiter = None, None
    if gateway is not None:
        try:
            gateway.close()
        except Exception:  # pragma: no cover - best effort cleanup
            logger.debug("Ignoring error while closing the SEC gateway.")
    if limiter is not None:
        try:
            limiter.close()
        except Exception:  # pragma: no cover - best effort cleanup
            logger.debug("Ignoring error while closing the SEC limiter.")


# ── Convenience API used by the SEC clients ─────────────────────────────────


def acquire_sec_request_slot(
    max_wait_seconds: float | None = None,
) -> SECRateLimitGrant:
    """Acquire one distributed SEC request slot from the shared limiter.

    Used by SEC clients whose HTTP stack cannot be routed through
    :meth:`SECRequestGateway.request` (for example third-party libraries that
    own their own transport).
    """
    return get_sec_rate_limiter().acquire(max_wait_seconds=max_wait_seconds)


def sec_http_request(method: str, url: str, **kwargs: Any) -> requests.Response:
    """Send a rate-limited SEC request through the central gateway."""
    return get_sec_gateway().request(method, url, **kwargs)


def sec_http_get(url: str, **kwargs: Any) -> requests.Response:
    """Send a rate-limited ``GET`` to the SEC through the central gateway."""
    return get_sec_gateway().get(url, **kwargs)


def sec_http_get_text(url: str, **kwargs: Any) -> str:
    """Fetch SEC text through the central gateway."""
    return get_sec_gateway().get_text(url, **kwargs)


def sec_http_get_json(url: str, **kwargs: Any) -> Any:
    """Fetch SEC JSON through the central gateway."""
    return get_sec_gateway().get_json(url, **kwargs)


async def sec_http_aget_text(url: str, **kwargs: Any) -> str:
    """Async twin of :func:`sec_http_get_text` (same distributed limit)."""
    return await get_sec_gateway().aget_text(url, **kwargs)


# ── edgartools enforcement ──────────────────────────────────────────────────
#
# SECClient / SECDownloader / SECLoader are served by SECRequestGateway
# directly. EdgarClient drives the third-party ``edgartools`` package, which
# owns its own httpx transport. The helpers below bind that transport (and the
# raw httpx call sites inside edgartools) to the same centralized Redis
# limiter, so the edgartools path cannot bypass the 10 req/s control.

_EDGAR_GUARDED_ORIGINALS: list[tuple[Any, str, Any]] = []
_active_enforcement_gateway: SECRequestGateway | None = None


def _active_gateway() -> SECRequestGateway:
    """Return the gateway currently bound to the edgartools helpers."""
    gateway = _active_enforcement_gateway
    return gateway if gateway is not None else get_sec_gateway()


class EdgarToolsRateLimiterAdapter:
    """``pyrate-limiter`` compatible adapter backed by the SEC limiter.

    edgartools (through ``httpxthrottlecache``) calls ``try_acquire`` for every
    HTTP request it makes - including its own internal retries - so binding
    this adapter makes all of that traffic pass through the distributed
    Redis-enforced limit.
    """

    def __init__(self, limiter: Any | None = None) -> None:
        self._limiter = limiter if limiter is not None else get_sec_rate_limiter()

    @property
    def limiter(self) -> Any:
        return self._limiter

    def try_acquire(
        self,
        name: str = "sec",
        weight: int = 1,
        blocking: bool = True,
        timeout: float | None = None,
    ) -> bool:
        """Block until the distributed limiter admits one SEC request."""
        self._limiter.acquire()
        return True

    async def try_acquire_async(
        self,
        name: str = "sec",
        weight: int = 1,
        timeout: float | None = None,
    ) -> bool:
        """Async twin of :meth:`try_acquire` using the same Redis key."""
        acquire_async = getattr(self._limiter, "acquire_async", None)
        if callable(acquire_async):
            await acquire_async()
        else:  # pragma: no cover - custom limiters may only be sync
            await asyncio.to_thread(self._limiter.acquire)
        return True


def _guard_module_function(module: Any, name: str, replacement: Any) -> bool:
    original = getattr(module, name, None)
    if original is None or getattr(original, "__sec_gateway_guarded__", False):
        return False
    replacement.__sec_gateway_guarded__ = True
    _EDGAR_GUARDED_ORIGINALS.append((module, name, original))
    setattr(module, name, replacement)
    return True


def _guard_class_method(cls: Any, name: str, replacement: Any) -> bool:
    original = getattr(cls, name, None)
    if original is None or getattr(original, "__sec_gateway_guarded__", False):
        return False
    replacement.__sec_gateway_guarded__ = True
    _EDGAR_GUARDED_ORIGINALS.append((cls, name, original))
    setattr(cls, name, replacement)
    return True


def _install_raw_edgar_guards(gateway: SECRequestGateway) -> None:
    """Route edgartools' raw httpx call sites through the central gateway.

    edgartools contains two places that create a fresh ``httpx`` client and
    therefore skip its own rate limiter entirely:
    ``edgar.sgml.sgml_common._fetch_url_directly`` and
    ``edgar.xmlfiling.XmlFiling.to_html``.
    """
    global _active_enforcement_gateway
    _active_enforcement_gateway = gateway

    try:
        from edgar.sgml import sgml_common

        def _fetch_url_directly(url: str) -> str:
            headers: dict[str, str] | None = None
            try:
                from edgar.core import get_identity

                identity = get_identity()
                if identity:
                    headers = {"User-Agent": identity}
            except Exception:  # pragma: no cover - identity is optional here
                headers = None
            return _active_gateway().get_text(url, headers=headers)

        _guard_module_function(sgml_common, "_fetch_url_directly", _fetch_url_directly)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Could not guard edgartools' direct SGML fetch: %s", exc)

    try:
        import importlib

        xmlfiling = importlib.import_module("edgar.xmlfiling")

        cls = getattr(xmlfiling, "XmlFiling", None)
        if cls is not None:
            original_to_html = cls.to_html

            def _to_html(self: Any) -> Any:
                if not getattr(self, "_xslt_prefix", None):
                    return None
                # The wrapped implementation performs exactly one raw SEC
                # request, so it consumes exactly one admission slot.
                _active_gateway().limiter.acquire()
                return original_to_html(self)

            _to_html.__doc__ = original_to_html.__doc__
            _guard_class_method(cls, "to_html", _to_html)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Could not guard edgartools' XSLT HTML fetch: %s", exc)


def install_edgar_sec_enforcement(gateway: SECRequestGateway | None = None) -> bool:
    """Bind every edgartools HTTP request to the centralized SEC gateway.

    Returns:
        True when the enforcement hook was installed (or already present),
        False when edgartools is not importable.
    """
    gateway = gateway if gateway is not None else get_sec_gateway()

    try:
        from edgar.httpclient import HTTP_MGR
    except Exception as exc:
        logger.warning("edgartools is unavailable; no edgartools SEC enforcement: %s", exc)
        return False

    # Never allow edgartools' own rate limiter to be switched off.
    HTTP_MGR.rate_limiter_enabled = True

    already_bound = isinstance(
        getattr(HTTP_MGR, "rate_limiter", None), EdgarToolsRateLimiterAdapter
    )
    HTTP_MGR.rate_limiter = EdgarToolsRateLimiterAdapter(gateway.limiter)

    if not already_bound:
        # Drop any client/transport built with edgartools' own process-local
        # limiter so the next request uses the centralized limiter.
        try:
            HTTP_MGR.close()
        except Exception:  # pragma: no cover - best effort cleanup
            logger.debug("Ignoring error while resetting the edgartools HTTP client.")

    _install_raw_edgar_guards(gateway)

    logger.info(
        "edgartools SEC traffic is bound to the centralized SEC gateway (key=%s).",
        getattr(gateway.limiter, "key", "n/a"),
    )
    return True


def uninstall_edgar_sec_enforcement() -> None:
    """Restore the original edgartools helpers (test/teardown helper)."""
    while _EDGAR_GUARDED_ORIGINALS:
        target, name, original = _EDGAR_GUARDED_ORIGINALS.pop()
        try:
            setattr(target, name, original)
        except Exception:  # pragma: no cover - best effort teardown
            logger.debug("Could not restore %s on %r", name, target)


__all__ = [
    "EdgarToolsRateLimiterAdapter",
    "RedisStrictRateLimiter",
    "SECRateLimitGrant",
    "SECRateLimitUnavailableError",
    "SECRateLimiter",
    "SECRequestFailedError",
    "SECRequestGateway",
    "SECRequestNotAllowedError",
    "SECHttpTransport",
    "SEC_HOSTS",
    "SEC_MAX_REQUESTS_PER_SECOND",
    "SEC_RATE_LIMIT_REDIS_KEY",
    "SEC_RATE_LIMIT_WINDOW_SECONDS",
    "acquire_sec_request_slot",
    "ensure_sec_url",
    "get_sec_gateway",
    "get_sec_rate_limiter",
    "install_edgar_sec_enforcement",
    "is_sec_url",
    "reset_sec_gateway",
    "sec_http_aget_text",
    "sec_http_get",
    "sec_http_get_json",
    "sec_http_get_text",
    "sec_http_request",
    "set_sec_gateway",
    "set_sec_rate_limiter",
    "uninstall_edgar_sec_enforcement",
]
