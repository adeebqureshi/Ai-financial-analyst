from unittest.mock import MagicMock
from unittest.mock import patch

from app.retrieval.hybrid_retriever import HybridRetriever


@patch("app.retrieval.hybrid_retriever.DenseRetriever")
def test_hybrid(mock_dense):

    dense = MagicMock()

    point = MagicMock()
    point.id = "1"

    dense.search.return_value = [point]

    mock_dense.return_value = dense

    retriever = HybridRetriever()

    retriever.build(
        ["1"],
        ["Apple revenue"],
    )

    results = retriever.search(
        [0.1, 0.2],
        "Apple revenue",
    )

    assert "1" in results