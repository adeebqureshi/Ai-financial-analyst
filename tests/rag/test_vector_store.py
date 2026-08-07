from app.rag.embedding import Embedding
from app.rag.memory_store import MemoryVectorStore


def test_store():

    store = MemoryVectorStore()

    store.add(
        Embedding(
            text="Apple",
            vector=[1.0, 2.0],
        )
    )

    assert store.size == 1