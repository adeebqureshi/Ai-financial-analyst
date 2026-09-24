from unittest.mock import MagicMock, patch
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
@patch("app.llm.providers.openai_provider.os.getenv", return_value="fake-key")
@patch("app.llm.providers.openai_provider.OpenAI")
def test_openai_stream(mock_openai, mock_getenv):
    client = MagicMock()
    mock_openai.return_value = client
    # OpenAIProvider.generate() uses the chat.completions API and reads
    # choices[0].message.content — mirror that exact response shape here.
    message = MagicMock()
    message.content = "Hello World"
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    response.model = "test-model"
    client.chat.completions.create.return_value = response
    provider = OpenAIProvider()
    tokens = list(
        provider.stream(
            LLMRequest(prompt="Hello World")
        )
    )
    assert len(tokens) > 0
    assert "".join(tokens).strip() == "Hello World"