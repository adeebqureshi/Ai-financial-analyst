"""
async_interfaces.py

Asynchronous LLM interface definitions.

The async layer mirrors the synchronous ``BaseLLMProvider`` contract but adds
real token/chunk streaming. Providers implement two methods:

- ``generate`` — return the complete response as ``LLMResponse``.
- ``stream`` — yield progressive text deltas as ``AsyncIterator[str]``.

Design Decisions:
    - **Async throughout**: Both methods are native ``async`` so providers can
      hold an ``AsyncOpenAI`` (or equivalent) client without blocking the event
      loop. ``stream`` is an async generator — it never fakes streaming by
      chunking a pre-completed response.
    - **Same request/response models**: ``LLMRequest`` / ``LLMResponse`` are
      reused from the synchronous layer so the request contract is identical
      for sync and async callers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.llm.models import LLMRequest, LLMResponse


class AsyncLLMProvider(ABC):
    """
    Contract for asynchronous LLM providers.
    """

    @abstractmethod
    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        Generate a complete LLM response.

        Args:
            request: The LLM request.

        Returns:
            The complete ``LLMResponse``.
        """

    @abstractmethod
    def stream(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[str]:
        """
        Stream an LLM response token-by-token.

        Args:
            request: The LLM request.

        Yields:
            Progressive text deltas. Concatenating every yielded string
            reproduces the full response.
        """
