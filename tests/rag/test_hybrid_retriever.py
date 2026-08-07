from app.rag.embedding import Embedding
from app.rag.hybrid_retriever import HybridRetriever


def test_hybrid():

    docs = [
        Embedding(
            text="Apple revenue increased",
            vector=[1.0, 0.0],
        ),
        Embedding(
            text="Microsoft Azure",
            vector=[0.0, 1.0],
        ),
    ]

    query = Embedding(
        text="Apple revenue",
        vector=[1.0, 0.0],
    )

    retriever = HybridRetriever()

    results = retriever.search(
        query,
        docs,
    )

    assert len(results) == 2

    assert results[0].embedding.text == "Apple revenue increased"