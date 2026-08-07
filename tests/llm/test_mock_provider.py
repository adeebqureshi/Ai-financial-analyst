from app.llm.models import LLMRequest
from app.llm.providers.mock import MockLLMProvider


def test_mock_provider():

    provider = MockLLMProvider()

    response = provider.generate(
        LLMRequest(
            prompt="Hello",
        )
    )

    assert response.model == "mock-llm"
    assert "Hello" in response.text