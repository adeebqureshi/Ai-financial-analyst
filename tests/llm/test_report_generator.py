import pytest

from app.llm.providers.factory import ProviderFactory
from app.llm.providers.mock import MockLLMProvider
from app.llm.providers.openai_provider import OpenAIProvider


def test_mock():
    provider = ProviderFactory.create("mock")
    assert isinstance(provider, MockLLMProvider)


def test_openai():
    provider = ProviderFactory.create("openai")
    assert isinstance(provider, OpenAIProvider)


def test_invalid():
    with pytest.raises(ValueError):
        ProviderFactory.create("xyz")