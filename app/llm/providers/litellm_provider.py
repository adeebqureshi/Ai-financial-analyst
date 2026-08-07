"""
LiteLLM provider.
"""

from __future__ import annotations

from app.llm.models import LLMRequest
from app.llm.models import LLMResponse
from app.llm.providers.base import BaseLLMProvider


class LiteLLMProvider(BaseLLMProvider):

    MODEL = "litellm"

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        return LLMResponse(
            text=f"LITELLM_RESPONSE:\n\n{request.prompt}",
            model=self.MODEL,
        )