import pytest

from app.llm.providers.factory import ProviderFactory
from app.llm.providers.mock import MockLLMProvider
from app.llm.providers.ollama_provider import OllamaProvider
from app.llm.providers.openai_provider import OpenAIProvider
from app.llm.providers.vllm_provider import VLLMProvider


def test_mock():

    provider = ProviderFactory.create("mock")

    assert isinstance(provider, MockLLMProvider)


def test_openai():

    provider = ProviderFactory.create("openai")

    assert isinstance(provider, OpenAIProvider)


def test_ollama():

    provider = ProviderFactory.create("ollama")

    assert isinstance(provider, OllamaProvider)


def test_vllm():

    provider = ProviderFactory.create("vllm")

    assert isinstance(provider, VLLMProvider)


def test_invalid():

    with pytest.raises(ValueError):

        ProviderFactory.create("xyz")