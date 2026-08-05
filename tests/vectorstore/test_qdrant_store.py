from app.vectorstore.qdrant_store import QdrantStore


def test_upsert_and_search():

    store = QdrantStore(
        vector_size=3,
    )

    store.upsert(
        ids=[1],
        vectors=[[0.1, 0.2, 0.3]],
        payloads=[
            {
                "ticker": "AAPL",
            }
        ],
    )

    results = store.search(
        [0.1, 0.2, 0.3],
        limit=1,
    )

    assert len(results) == 1

    assert results[0].payload["ticker"] == "AAPL"