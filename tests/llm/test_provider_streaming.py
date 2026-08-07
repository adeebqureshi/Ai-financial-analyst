from app.llm.models import LLMRequest
from app.llm.providers.mock import MockLLMProvider
from app.llm.providers.openai_provider import OpenAIProvider


def test_mock_stream():

    provider = MockLLMProvider()

    tokens = list(
        provider.stream(
            LLMRequest(prompt="Hello World")
        )
    )

    assert len(tokens) > 0


def test_openai_stream():

    provider = OpenAIProvider()

    tokens = list(
        provider.stream(
            LLMRequest(prompt="Hello World")
        )
    )

    assert len(tokens) > 0