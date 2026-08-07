from app.llm.models import LLMRequest
from app.llm.providers.ollama_provider import OllamaProvider


def test_ollama_provider():

    provider = OllamaProvider()

    response = provider.generate(
        LLMRequest(
            prompt="Hello",
        )
    )

    assert response.model == "ollama"
    assert "Hello" in response.text