from app.rag.embedding import Embedding
from app.rag.embedding_cache import EmbeddingCache


def test_cache():

    cache = EmbeddingCache()

    embedding = Embedding(
        text="Revenue",
        vector=[1.0, 2.0],
    )

    cache.put(embedding)

    assert cache.size == 1

    assert cache.get("Revenue") is embedding


def test_clear():

    cache = EmbeddingCache()

    cache.put(
        Embedding(
            text="A",
            vector=[1],
        )
    )

    cache.clear()

    assert cache.size == 0