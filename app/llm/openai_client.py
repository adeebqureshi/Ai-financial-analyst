"""
openai_client.py

Mock OpenAI implementation.
"""

from __future__ import annotations

from app.llm.interfaces import LLMProvider
from app.llm.models import LLMRequest
from app.llm.models import LLMResponse


class OpenAIClient(LLMProvider):

    MODEL = "mock-llm"

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        return LLMResponse(
            text=f"LLM_RESPONSE:\n\n{request.prompt}",
            model=self.MODEL,
        )