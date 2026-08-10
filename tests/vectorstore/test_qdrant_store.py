import uuid

from app.vectorstore.qdrant_store import QdrantStore


def test_upsert_and_search():

    store = QdrantStore(
        collection_name=f"test_qdrant_{uuid.uuid4().hex[:8]}",
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


def test_document_filter_and_delete():

    store = QdrantStore(
        collection_name=f"test_qdrant_{uuid.uuid4().hex[:8]}",
        vector_size=3,
    )

    store.upsert(
        ids=[101, 202],
        vectors=[[0.1, 0.2, 0.3], [0.3, 0.2, 0.1]],
        payloads=[
            {"document_id": "a", "chunk_id": "a:0", "text": "apple"},
            {"document_id": "b", "chunk_id": "b:0", "text": "banana"},
        ],
    )

    scoped = store.search(
        [0.1, 0.2, 0.3],
        limit=5,
        document_id="a",
    )

    assert len(scoped) == 1

    assert scoped[0].payload["document_id"] == "a"

    store.delete_by_document_id("a")

    remaining = store.get_all()

    assert len(remaining) == 1

    assert remaining[0].payload["document_id"] == "b"
