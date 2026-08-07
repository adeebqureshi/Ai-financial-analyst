"""
Base interface for all LLM providers.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Iterator

from app.llm.models import LLMRequest
from app.llm.models import LLMResponse


class BaseLLMProvider(ABC):

    @abstractmethod
    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """Generate a complete response."""

    def stream(
        self,
        request: LLMRequest,
    ) -> Iterator[str]:
        """
        Default streaming implementation.

        Providers that support native streaming should override this method.
        """

        response = self.generate(request)

        for token in response.text.split():
            yield token + " "