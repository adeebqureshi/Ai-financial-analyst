from app.llm.models import LLMRequest
from app.llm.providers.mock import MockLLMProvider


def test_stream():

    provider = MockLLMProvider()

    tokens = list(
        provider.stream(
            LLMRequest(
                prompt="Hello World"
            )
        )
    )

    assert len(tokens) > 0

    assert "".join(tokens).strip() != ""