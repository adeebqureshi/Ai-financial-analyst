import pytest

from app.llm.exceptions import ProviderError
from app.llm.models import LLMRequest
from app.llm.providers.openai_provider import OpenAIProvider


def test_openai_provider_missing_key_fails_fast():

    provider = OpenAIProvider()

    # Without an OPENAI_API_KEY the real provider must NOT silently echo the
    # prompt — it raises a typed, key-free error the caller can degrade on.
    assert provider.client is None

    with pytest.raises(ProviderError):
        provider.generate(
            LLMRequest(
                prompt="Hello",
            )
        )
