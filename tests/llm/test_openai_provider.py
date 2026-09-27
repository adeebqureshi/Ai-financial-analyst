import pytest

from app.llm.exceptions import ProviderError
from app.llm.models import LLMRequest
from app.llm.providers.openai_provider import OpenAIProvider


def test_openai_provider_missing_key_fails_fast(monkeypatch):
    # Hermetic: clear every credential the provider may read, so the test
    # asserts the missing-key behaviour regardless of the developer's shell.
    for var in (
        "OPENAI_API_KEY",
        "FREELLMAPI_API_KEY",
        "FREELLMAPI_BASE_URL",
    ):
        monkeypatch.delenv(var, raising=False)

    provider = OpenAIProvider()
    assert provider.client is None

    with pytest.raises(ProviderError):
        provider.generate(
            LLMRequest(
                prompt="Hello",
            )
        )