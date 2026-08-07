from app.llm.models import LLMRequest
from app.llm.providers.anthropic_provider import AnthropicProvider


def test_anthropic_provider():

    provider = AnthropicProvider()

    response = provider.generate(
        LLMRequest(
            prompt="Hello",
        )
    )

    assert response.model == "anthropic"
    assert "Hello" in response.text