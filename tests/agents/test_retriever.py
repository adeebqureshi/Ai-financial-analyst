from unittest.mock import MagicMock
from unittest.mock import patch

from app.agents.retriever import RetrieverAgent


@patch("app.agents.retriever.RetrievalEngine")
def test_retrieve(mock_engine):

    engine = MagicMock()

    engine.retrieve.return_value = "context"

    mock_engine.return_value = engine

    agent = RetrieverAgent()

    result = agent.retrieve(
        "Apple revenue"
    )

    assert result == "context"

    engine.retrieve.assert_called_once_with(
        query="Apple revenue",
        limit=5,
    )