"""
Async provider factory.

Registers the asynchronous providers supported by the streaming chat layer and
constructs them by name. This mirrors the synchronous ``ProviderFactory`` for
the async side — the streaming endpoint selects its provider from the same
``LLM_PROVIDER`` configuration key.

Registered providers:
    - ``mock``   -> :class:`AsyncMockLLMProvider` (offline, deterministic).
    - ``openai`` -> :class:`AsyncOpenAIProvider` (real, ``AsyncOpenAI``).
"""

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
        """Register (or replace) an async provider by name."""
        cls._providers[name.lower()] = provider

    @classmethod
    def create(
        cls,
        name: str,
        **kwargs: object,
    ) -> AsyncLLMProvider:
        """
        Build an async provider instance by name.

        Args:
            name: Provider name (``mock``, ``openai``, or a registered alias).
            **kwargs: Extra keyword arguments forwarded to the provider
                constructor (e.g. ``api_key`` for the OpenAI provider).

        Returns:
            A fresh provider instance.

        Raises:
            ValueError: If the provider name is not registered.
        """
        key = name.lower()

        if key not in cls._providers:
            raise ValueError(f"Unknown async provider: {name}")

        return cls._providers[key](**kwargs)
