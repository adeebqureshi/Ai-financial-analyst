import pytest

from app.llm.providers.factory import (
    PRIMARY_PROVIDER,
    SUPPORTED_PROVIDERS,
    ProviderFactory,
)
from app.llm.providers.mock import MockLLMProvider
from app.llm.providers.openai_provider import OpenAIProvider


def test_primary_provider_is_openai():
    assert PRIMARY_PROVIDER == "openai"


def test_supported_providers_are_limited_to_openai_and_mock():
    assert set(SUPPORTED_PROVIDERS) == {"openai", "mock"}


def test_mock():
    assert isinstance(
        ProviderFactory.create("mock"),
        MockLLMProvider,
    )


def test_openai():
    assert isinstance(
        ProviderFactory.create("openai"),
        OpenAIProvider,
    )


def test_invalid():
    with pytest.raises(ValueError):
        ProviderFactory.create("xyz")


def test_removed_stub_providers_are_no_longer_registered():
    # The stub providers (anthropic/gemini/litellm/ollama/vllm) only echoed the
    # prompt back. They are gone, so the factory must reject them.
    for removed in ("anthropic", "gemini", "litellm", "ollama", "vllm", "google"):
        with pytest.raises(ValueError):
            ProviderFactory.create(removed)