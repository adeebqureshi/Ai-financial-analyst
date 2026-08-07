from app.rag.embedding import Embedding
from app.rag.memory_store import MemoryVectorStore


def test_search():

    store = MemoryVectorStore()

    store.add(
        Embedding(
            text="Revenue",
            vector=[1.0],
        )
    )

    query = Embedding(
        text="Revenue",
        vector=[1.0],
    )

    results = store.search(query)

    assert len(results) == 1

    assert results[0].text == "Revenue"


def test_clear():

    store = MemoryVectorStore()

    store.add(
        Embedding(
            text="A",
            vector=[1],
        )
    )

    store.clear()

    assert store.size == 0