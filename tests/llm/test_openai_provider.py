import pytest
from app.llm.exceptions import ProviderError
from app.llm.models import LLMRequest
from app.llm.providers.openai_provider import OpenAIProvider
def test_openai_provider_missing_key_fails_fast():
    provider = OpenAIProvider()
    assert provider.client is None
    with pytest.raises(ProviderError):
        provider.generate(
            LLMRequest(
                prompt="Hello",
            )
        )