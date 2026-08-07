"""
Workflow retry.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class WorkflowRetry:

    def __init__(
        self,
        attempts: int = 3,
    ) -> None:

        self.attempts = attempts

    def execute(
        self,
        func: Callable[[], T],
    ) -> T:

        last_error: Exception | None = None

        for _ in range(self.attempts):

            try:
                return func()

            except Exception as exc:
                last_error = exc

        assert last_error is not None

        raise last_error