from app.llm.providers.factory import ProviderFactory
from app.llm.providers.mock import MockLLMProvider


def test_factory_uses_registry():

    provider = ProviderFactory.create("mock")

    assert isinstance(provider, MockLLMProvider)