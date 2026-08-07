"""
LLM client.
"""

from __future__ import annotations

from app.llm.models import LLMRequest
from app.llm.models import LLMResponse
from app.llm.providers.mock import MockLLMProvider
from app.llm.provider_config import ProviderConfig

...

class OpenAIClient:

    def __init__(
        self,
        config: ProviderConfig | None = None,
    ) -> None:

        self.config = config or ProviderConfig()

        self.provider = ProviderFactory.create(
            self.config.provider,
        )


class OpenAIClient:

    def __init__(self) -> None:

        self.provider = MockLLMProvider()

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        return self.provider.generate(request)