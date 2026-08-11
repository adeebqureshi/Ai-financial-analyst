"""
LLM client.

``OpenAIClient`` is the thin entry point used by the agents. It delegates to
whichever provider is configured via ``LLM_PROVIDER``:

- default ``mock`` (used by tests and offline development),
- ``openai`` (or any name registered in ``ProviderFactory``) in production.

The abstraction/interface is preserved: callers use ``generate`` / ``stream``
on a ``BaseLLMProvider`` under the hood.
"""

from __future__ import annotations

from collections.abc import Iterator

from app.core.config import Settings, get_settings
from app.llm.models import LLMRequest, LLMResponse
from app.llm.provider_config import ProviderConfig
from app.llm.providers.base import BaseLLMProvider
from app.llm.providers.factory import ProviderFactory


class OpenAIClient:

    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
        config: ProviderConfig | None = None,
        settings: Settings | None = None,
    ) -> None:
        """
        Build the client around the configured provider.

        Args:
            provider: An explicit provider instance (tests inject mocks here).
            config: An explicit ``ProviderConfig``; defaults to one built from
                application settings (``LLM_PROVIDER``, ``LLM_MODEL``, ...).
            settings: Optional settings source; defaults to the singleton.
        """
        settings = settings or get_settings()

        self.config = config or ProviderConfig.from_settings(settings)

        self.provider = provider or ProviderFactory.create(self.config.provider)

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        return self.provider.generate(request)

    def stream(
        self,
        request: LLMRequest,
    ) -> Iterator[str]:

        return self.provider.stream(request)
