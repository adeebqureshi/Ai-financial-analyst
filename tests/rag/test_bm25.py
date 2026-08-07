from app.rag.bm25 import BM25Retriever
from app.rag.embedding import Embedding


def test_bm25():

    docs = [
        Embedding(
            text="Apple revenue increased",
            vector=[1.0],
        ),
        Embedding(
            text="Microsoft cloud business",
            vector=[2.0],
        ),
    ]

    retriever = BM25Retriever()

    results = retriever.search(
        "Apple revenue",
        docs,
    )

    assert results[0].text == "Apple revenue increased"