from app.llm.models import LLMRequest
from app.llm.providers.gemini_provider import GeminiProvider


def test_gemini_provider():

    provider = GeminiProvider()

    response = provider.generate(
        LLMRequest(
            prompt="Hello Gemini",
        )
    )

    assert response.model == "gemini"
    assert "Hello Gemini" in response.text