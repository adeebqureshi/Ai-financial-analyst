from app.llm.models import LLMRequest
from app.llm.providers.openai_provider import OpenAIProvider


def test_openai_provider():

    provider = OpenAIProvider()

    response = provider.generate(
        LLMRequest(
            prompt="Hello",
        )
    )

    assert response.model == "openai"
    assert "Hello" in response.text