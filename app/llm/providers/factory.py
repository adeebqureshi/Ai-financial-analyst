from __future__ import annotations
from app.core.constants import DEFAULT_LLM_PROVIDER, SUPPORTED_LLM_PROVIDERS
from app.llm.provider_registry import ProviderRegistry
from app.llm.providers.base import BaseLLMProvider
from app.llm.providers.mock import MockLLMProvider
from app.llm.providers.openai_provider import OpenAIProvider

PRIMARY_PROVIDER = DEFAULT_LLM_PROVIDER
SUPPORTED_PROVIDERS = SUPPORTED_LLM_PROVIDERS


class ProviderFactory:
    _registry = ProviderRegistry()
    _registry.register("mock", MockLLMProvider)
    _registry.register(PRIMARY_PROVIDER, OpenAIProvider)

    @classmethod
    def create(
        cls,
        provider: str,
        **kwargs: object,
    ) -> BaseLLMProvider:
        return cls._registry.create(provider, **kwargs)
