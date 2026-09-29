from __future__ import annotations
import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar
from app.core.logging import get_logger
from app.llm.exceptions import (
    AuthenticationError,
    ProviderError,
    RateLimitError,
    TimeoutError,
)
logger = get_logger("app.llm.retry")
T = TypeVar("T")


class EmptyContentError(ProviderError):
        pass


class RetryPolicy:
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 30.0,
    ) -> None:
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay

    def _delay_for(self, exc: Exception, delay: float) -> float:
        """Choose the wait before the next attempt.

        Rate limits are special: the provider usually tells us exactly when
        the quota window resets. Sleeping for less than that guarantees the
        retry fails too, so the advised wait wins over the local backoff.
        """
        advised = getattr(exc, "retry_after", None)
        if isinstance(exc, RateLimitError) and advised:
            delay = max(delay, float(advised))
        return min(delay, self.max_delay)

    def execute(
        self,
        func: Callable[[], T],
    ) -> T:
        delay = self.base_delay
        for attempt in range(self.max_attempts):
            try:
                return func()
            except (TimeoutError, RateLimitError) as exc:
                if attempt == self.max_attempts - 1:
                    raise
                delay = self._delay_for(exc, delay)
                logger.warning(
                    "Transient failure, retrying: attempt=%d/%d delay=%.1fs "
                    "error_type=%s",
                    attempt + 1,
                    self.max_attempts,
                    delay,
                    exc.__class__.__name__,
                )
                time.sleep(delay)
                delay *= self.backoff_factor
            except (ProviderError, EmptyContentError):
                raise
        raise RuntimeError("RetryPolicy reached an unexpected state.")

    async def execute_async(
        self,
        func: Callable[[], Awaitable[T]],
    ) -> T:
        delay = self.base_delay
        for attempt in range(self.max_attempts):
            try:
                return await func()
            except (TimeoutError, RateLimitError) as exc:
                if attempt == self.max_attempts - 1:
                    raise
                delay = self._delay_for(exc, delay)
                logger.warning(
                    "Transient failure, retrying: attempt=%d/%d delay=%.1fs "
                    "error_type=%s",
                    attempt + 1,
                    self.max_attempts,
                    delay,
                    exc.__class__.__name__,
                )
                await asyncio.sleep(delay)
                delay *= self.backoff_factor
            except (ProviderError, EmptyContentError):
                raise
        raise RuntimeError("RetryPolicy reached an unexpected state.")
