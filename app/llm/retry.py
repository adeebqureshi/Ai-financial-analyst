from __future__ import annotations
import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar
from app.core.logging import get_logger
from app.llm.exceptions import ProviderError
from app.llm.exceptions import RateLimitError
from app.llm.exceptions import TimeoutError
logger = get_logger("app.llm.retry")
T = TypeVar("T")
class RetryPolicy:
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        backoff_factor: float = 2.0,
    ) -> None:
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
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
            except ProviderError:
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
            except ProviderError:
                raise
        raise RuntimeError("RetryPolicy reached an unexpected state.")