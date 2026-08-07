import pytest

from app.llm.providers.factory import ProviderFactory
from app.llm.providers.litellm_provider import LiteLLMProvider
from app.llm.providers.mock import MockLLMProvider
from app.llm.providers.ollama_provider import OllamaProvider
from app.llm.providers.openai_provider import OpenAIProvider
from app.llm.providers.vllm_provider import VLLMProvider
from app.llm.providers.anthropic_provider import AnthropicProvider
from app.llm.providers.gemini_provider import GeminiProvider

def test_gemini():

    provider = ProviderFactory.create("gemini")

    assert isinstance(provider, GeminiProvider)

def test_anthropic():

    provider = ProviderFactory.create("anthropic")

    assert isinstance(provider, AnthropicProvider)


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


def test_ollama():
    assert isinstance(
        ProviderFactory.create("ollama"),
        OllamaProvider,
    )


def test_vllm():
    assert isinstance(
        ProviderFactory.create("vllm"),
        VLLMProvider,
    )


def test_litellm():
    assert isinstance(
        ProviderFactory.create("litellm"),
        LiteLLMProvider,
    )


def test_invalid():

    with pytest.raises(ValueError):
        ProviderFactory.create("xyz")