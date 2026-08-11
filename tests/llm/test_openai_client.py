from app.llm.models import LLMRequest
from app.llm.openai_client import OpenAIClient
from app.llm.provider_config import ProviderConfig


def test_generate():

    # Explicitly use mock provider for unit tests so they never hit the network
    client = OpenAIClient(config=ProviderConfig(provider="mock"))

    response = client.generate(
        LLMRequest(prompt="Hello")
    )

    assert response.model == "mock-llm"
    assert response.text.startswith("LLM_RESPONSE")
    assert "Hello" in response.text