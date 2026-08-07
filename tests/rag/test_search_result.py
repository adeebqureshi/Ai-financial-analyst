from app.rag.embedding import Embedding
from app.rag.search_result import SearchResult


def test_result():

    result = SearchResult(
        embedding=Embedding(
            text="Apple",
            vector=[1.0],
        ),
        score=0.98,
    )

    assert result.score == 0.98

    assert result.embedding.text == "Apple"