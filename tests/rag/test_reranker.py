from app.rag.embedding import Embedding
from app.rag.reranker import Reranker
from app.rag.search_result import SearchResult


def test_rerank():

    reranker = Reranker()

    results = [
        SearchResult(
            embedding=Embedding(
                text="Microsoft Azure",
                vector=[0.0],
            ),
            score=0.2,
        ),
        SearchResult(
            embedding=Embedding(
                text="Apple revenue increased",
                vector=[1.0],
            ),
            score=0.1,
        ),
    ]

    reranked = reranker.rerank(
        "Apple revenue",
        results,
    )

    assert reranked[0].embedding.text == "Apple revenue increased"

    assert reranked[0].score > reranked[1].score