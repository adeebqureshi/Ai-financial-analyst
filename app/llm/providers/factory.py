from __future__ import annotations
from app.core.constants import DEFAULT_LLM_PROVIDER, SUPPORTED_LLM_PROVIDERS
from app.llm.provider_registry import ProviderRegistry
from app.llm.providers.base import BaseLLMProvider
from app.llm.providers.mock import MockLLMProvider
from app.llm.providers.openai_provider import OpenAIProvider

# Single primary LLM provider for the project.
#
# ``openai`` is the one real, fully-implemented provider: it performs real
# completions and also works against any OpenAI-compatible gateway (such as the
# bundled ``freellmapi`` service) via FREELLMAPI_BASE_URL / FREELLMAPI_API_KEY.
# ``mock`` is retained purely so the test-suite can run offline.
#
# Stub providers (anthropic / gemini / litellm / ollama / vllm) were removed:
# each one merely echoed the prompt back and produced no real completion, so
# they were dead code that made the provider list look larger than it was.
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