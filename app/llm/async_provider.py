from __future__ import annotations
from app.llm.async_interfaces import AsyncLLMProvider
from app.llm.providers.async_mock_provider import AsyncMockLLMProvider
from app.llm.providers.async_openai_provider import AsyncOpenAIProvider
class AsyncProviderFactory:
    _providers: dict[str, type[AsyncLLMProvider]] = {
        "mock": AsyncMockLLMProvider,
        "openai": AsyncOpenAIProvider,
    }
    @classmethod
    def register(
        cls,
        name: str,
        provider: type[AsyncLLMProvider],
    ) -> None:
        cls._providers[name.lower()] = provider
    @classmethod
    def create(
        cls,
        name: str,
        **kwargs: object,
    ) -> AsyncLLMProvider:
        key = name.lower()
        if key not in cls._providers:
            raise ValueError(f"Unknown async provider: {name}")
        return cls._providers[key](**kwargs)