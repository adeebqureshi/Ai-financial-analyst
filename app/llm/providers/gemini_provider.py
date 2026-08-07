"""
Gemini provider.
"""

from __future__ import annotations

from app.llm.models import LLMRequest
from app.llm.models import LLMResponse
from app.llm.providers.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):

    MODEL = "gemini"

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        return LLMResponse(
            text=f"GEMINI_RESPONSE:\n\n{request.prompt}",
            model=self.MODEL,
        )