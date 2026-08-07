"""
Mock LLM provider.
"""

from __future__ import annotations

from collections.abc import Iterator

from app.llm.models import LLMRequest
from app.llm.models import LLMResponse
from app.llm.providers.base import BaseLLMProvider
from app.llm.usage import TokenUsage


class MockLLMProvider(BaseLLMProvider):

    MODEL = "mock-llm"

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        return LLMResponse(
    text=f"LLM_RESPONSE:\n\n{request.prompt}",
    model=self.MODEL,
    usage=TokenUsage(
        prompt_tokens=len(request.prompt.split()),
        completion_tokens=5,
    ),
)

    def stream(
        self,
        request: LLMRequest,
    ) -> Iterator[str]:

        response = self.generate(request)

        for token in response.text.split():
            yield token + " "