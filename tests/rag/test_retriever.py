from app.rag.embedding import Embedding
from app.rag.retriever import Retriever


def test_retriever():

    retriever = Retriever()

    query = Embedding(
        text="query",
        vector=[1.0, 0.0],
    )

    docs = [
        Embedding(
            text="A",
            vector=[1.0, 0.0],
        ),
        Embedding(
            text="B",
            vector=[0.0, 1.0],
        ),
    ]

    results = retriever.search(
        query,
        docs,
    )

    assert results[0].embedding.text == "A"

    assert results[0].score > results[1].score