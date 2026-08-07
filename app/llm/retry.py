"""
Retry utilities for LLM providers.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from app.llm.exceptions import ProviderError
from app.llm.exceptions import RateLimitError
from app.llm.exceptions import TimeoutError

T = TypeVar("T")


class RetryPolicy:
    """
    Retry policy with exponential backoff.
    """

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

            except (TimeoutError, RateLimitError):
                if attempt == self.max_attempts - 1:
                    raise

                time.sleep(delay)
                delay *= self.backoff_factor

            except ProviderError:
                raise

        raise RuntimeError("RetryPolicy reached an unexpected state.")