from unittest.mock import MagicMock
from unittest.mock import patch

from app.llm.models import LLMRequest
from app.llm.providers.openai_provider import OpenAIProvider


@patch("app.llm.providers.openai_provider.os.getenv", return_value="fake-key")
@patch("app.llm.providers.openai_provider.OpenAI")
def test_generate(mock_openai, mock_getenv):
    client = MagicMock()
    mock_openai.return_value = client

    message = MagicMock()
    message.content = "Hello"
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    completion.model = "test-model"
    client.chat.completions.create.return_value = completion

    provider = OpenAIProvider()
    response = provider.generate(
        LLMRequest(
            prompt="Hi",
        )
    )
    assert response.text == "Hello"
    assert response.model == "test-model"
    # Must use the chat.completions API (not the legacy responses API).
    client.chat.completions.create.assert_called_once()