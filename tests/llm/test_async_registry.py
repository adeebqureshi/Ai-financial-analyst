"""
Async provider registry tests.

Covers :class:`AsyncProviderFactory` name resolution for the streaming layer.
"""

import pytest

from app.llm.async_provider import AsyncProviderFactory
from app.llm.providers.async_mock_provider import AsyncMockLLMProvider
from app.llm.providers.async_openai_provider import AsyncOpenAIProvider


def test_async_factory_creates_mock_provider():
    provider = AsyncProviderFactory.create("mock")

    assert isinstance(provider, AsyncMockLLMProvider)


def test_async_factory_creates_openai_provider():
    provider = AsyncProviderFactory.create("openai")

    assert isinstance(provider, AsyncOpenAIProvider)


def test_async_factory_is_case_insensitive():
    assert isinstance(AsyncProviderFactory.create("Mock"), AsyncMockLLMProvider)
    assert isinstance(AsyncProviderFactory.create("OPENAI"), AsyncOpenAIProvider)


def test_async_factory_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown async provider"):
        AsyncProviderFactory.create("does-not-exist")


def test_async_factory_register_custom_provider():
    class _CustomProvider(AsyncMockLLMProvider):
        pass

    AsyncProviderFactory.register("custom", _CustomProvider)

    assert isinstance(AsyncProviderFactory.create("custom"), _CustomProvider)
