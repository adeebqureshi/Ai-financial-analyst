"""
Per-user LLM token quota enforcement.

Complements the request-count rate limiter (``app.api.rate_limiter``) with a
token-based budget: chat requests consume an *estimated* token amount
(prompt tokens + reserved output tokens) against a configurable per-user
daily allowance. Accounting is in-process (thread-safe), mirroring the rate
limiter's local fallback semantics.

Design Decisions:
    - **Estimation, not accounting**: Quota is charged *before* the LLM call
      from the request size plus the configured output reserve
      (``llm_max_tokens``). Actual provider-reported usage is not yet
      available at that point, so the estimate intentionally errs high —
      a conservative guard against runaway cost.
    - **Authenticated users only**: Tokens cannot be attributed without an
      identity; unauthenticated traffic remains covered by per-IP request
      rate limiting.
    - **0 disables**: Setting ``llm_token_quota_per_user_per_day = 0`` turns
      the quota off entirely.
"""

from __future__ import annotations

import threading
import time

from app.core.config import Settings

_SECONDS_PER_DAY = 86_400


def _day_bucket() -> int:
    """Return the current UTC day bucket (days since epoch)."""
    return int(time.time() // _SECONDS_PER_DAY)


class TokenQuotaEnforcer:
    """
    Per-user daily token budget.

    Accounting is kept in a thread-safe in-memory map keyed by
    ``owner_id``/day. This matches the rate limiter's local fallback
    semantics: accurate within a process; cross-worker sharing requires a
    Redis-backed counter (see remaining-limitations note in the audit).
    """

    def __init__(self, daily_limit: int) -> None:
        self._daily_limit = daily_limit
        self._lock = threading.Lock()
        self._usage: dict[str, int] = {}

    @property
    def enabled(self) -> bool:
        return self._daily_limit > 0

    def consume(self, owner_id: str, tokens: int) -> bool:
        """
        Charge ``tokens`` against the user's daily budget.

        Returns:
            ``True`` when the charge fits within the remaining allowance
            (the charge is applied); ``False`` when the budget is exhausted
            (nothing is charged).
        """
        if not self.enabled:
            return True

        key = f"{owner_id}:{_day_bucket()}"

        with self._lock:
            projected = self._usage.get(key, 0) + tokens

            if projected > self._daily_limit:
                return False

            self._usage[key] = projected

        return True

    def remaining(self, owner_id: str) -> int:
        """Return the user's remaining token allowance for today."""
        if not self.enabled:
            return -1

        key = f"{owner_id}:{_day_bucket()}"

        with self._lock:
            return max(0, self._daily_limit - self._usage.get(key, 0))


# ──────────────────────────────────────────────────────────────────────────────
# Singleton access
# ──────────────────────────────────────────────────────────────────────────────

_token_quota: TokenQuotaEnforcer | None = None
_token_quota_lock = threading.Lock()


def get_token_quota(settings: Settings) -> TokenQuotaEnforcer:
    """Return the process-wide token quota enforcer."""
    global _token_quota

    with _token_quota_lock:
        if _token_quota is None:
            _token_quota = TokenQuotaEnforcer(
                settings.llm_token_quota_per_user_per_day,
            )
        return _token_quota


def reset_token_quota() -> None:
    """Reset the singleton (for testing)."""
    global _token_quota
    with _token_quota_lock:
        _token_quota = None