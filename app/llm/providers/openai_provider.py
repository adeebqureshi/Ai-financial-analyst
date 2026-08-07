"""
OpenAI provider.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

from openai import OpenAI

from app.llm.models import LLMRequest
from app.llm.models import LLMResponse
from app.llm.providers.base import BaseLLMProvider
from app.llm.retry import RetryPolicy
from app.llm.usage import TokenUsage


class OpenAIProvider(BaseLLMProvider):

    MODEL = "openai"

    def __init__(self) -> None:
        self.retry = RetryPolicy()
        self.client = None

        api_key = os.getenv("OPENAI_API_KEY")

        if api_key:
            self.client = OpenAI(api_key=api_key)

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        if self.client is None:
            return LLMResponse(
                text=f"OPENAI_RESPONSE:\n\n{request.prompt}",
                model=self.MODEL,
                usage=TokenUsage(
                    prompt_tokens=len(request.prompt.split()),
                    completion_tokens=2,
                ),
            )

        def call() -> LLMResponse:

            response = self.client.responses.create(
                model="gpt-5",
                input=request.prompt,
            )

            output = response.output_text

            return LLMResponse(
                text=output,
                model=self.MODEL,
                usage=TokenUsage(
                    prompt_tokens=len(request.prompt.split()),
                    completion_tokens=len(output.split()),
                ),
            )

        return self.retry.execute(call)

    def stream(
        self,
        request: LLMRequest,
    ) -> Iterator[str]:

        response = self.generate(request)

        for token in response.text.split():
            yield token + " "