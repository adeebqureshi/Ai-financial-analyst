from app.llm.models import LLMRequest
from app.llm.openai_client import OpenAIClient


def test_generate():

    client = OpenAIClient()

    response = client.generate(
        LLMRequest(prompt="Hello")
    )

    assert response.model == "mock-llm"
    assert response.text.startswith("LLM_RESPONSE")
    assert "Hello" in response.text