from unittest.mock import MagicMock
from unittest.mock import patch

from app.llm.models import LLMRequest
from app.llm.providers.openai_provider import OpenAIProvider


@patch("app.llm.providers.openai_provider.os.getenv", return_value="fake-key")
@patch("app.llm.providers.openai_provider.OpenAI")
def test_generate(mock_openai, mock_getenv):

    client = MagicMock()
    mock_openai.return_value = client

    client.responses.create.return_value.output_text = "Hello"

    provider = OpenAIProvider()

    response = provider.generate(
        LLMRequest(
            prompt="Hi",
        )
    )

    assert response.text == "Hello"
    assert response.model == "openai"