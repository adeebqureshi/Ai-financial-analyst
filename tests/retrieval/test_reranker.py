from unittest.mock import MagicMock
from unittest.mock import patch

from app.retrieval.reranker import Reranker


@patch("app.retrieval.reranker.CrossEncoder")
def test_rerank(mock_encoder):

    encoder = MagicMock()

    encoder.predict.return_value = [
        0.8,
        0.2,
    ]

    mock_encoder.return_value = encoder

    reranker = Reranker()

    results = reranker.rerank(
        "Apple revenue",
        [
            "Apple revenue increased.",
            "Tesla deliveries.",
        ],
    )

    assert results[0][0] == "Apple revenue increased."

    assert results[0][1] == 0.8