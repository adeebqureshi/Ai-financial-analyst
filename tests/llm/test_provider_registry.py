import pytest

from app.llm.providers.mock import MockLLMProvider
from app.llm.provider_registry import ProviderRegistry


def test_register():

    registry = ProviderRegistry()

    registry.register(
        "mock",
        MockLLMProvider,
    )

    provider = registry.create("mock")

    assert isinstance(provider, MockLLMProvider)


def test_unknown():

    registry = ProviderRegistry()

    with pytest.raises(ValueError):
        registry.create("abc")