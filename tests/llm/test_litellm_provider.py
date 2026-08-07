from app.llm.models import LLMRequest
from app.llm.providers.litellm_provider import LiteLLMProvider


def test_litellm_provider():

    provider = LiteLLMProvider()

    response = provider.generate(
        LLMRequest(
            prompt="Hello",
        )
    )

    assert response.model == "litellm"
    assert "Hello" in response.text