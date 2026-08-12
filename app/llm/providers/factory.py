"""
Provider factory.
"""

from __future__ import annotations

from app.llm.provider_registry import ProviderRegistry
from app.llm.providers.anthropic_provider import AnthropicProvider
from app.llm.providers.base import BaseLLMProvider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.providers.litellm_provider import LiteLLMProvider
from app.llm.providers.mock import MockLLMProvider
from app.llm.providers.ollama_provider import OllamaProvider
from app.llm.providers.openai_provider import OpenAIProvider
from app.llm.providers.vllm_provider import VLLMProvider


class ProviderFactory:

    _registry = ProviderRegistry()

    _registry.register("mock", MockLLMProvider)
    _registry.register("openai", OpenAIProvider)
    _registry.register("ollama", OllamaProvider)
    _registry.register("vllm", VLLMProvider)
    _registry.register("litellm", LiteLLMProvider)
    _registry.register("anthropic", AnthropicProvider)
    _registry.register("gemini", GeminiProvider)

    @classmethod
    def create(
        cls,
        provider: str,
        **kwargs: object,
    ) -> BaseLLMProvider:

        return cls._registry.create(provider, **kwargs)