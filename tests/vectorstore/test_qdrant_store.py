import uuid

import pytest

from app.core.exceptions import RetrievalError
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


class _Point:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_search_filters_malformed_points(monkeypatch):
    store = QdrantStore(collection_name=f"test_qdrant_{uuid.uuid4().hex[:8]}", vector_size=3)
    valid = _Point(id=1, score=0.8, payload={"text": "valid", "chunk_id": "a:0"})
    client = type("Client", (), {"query_points": lambda self, **kwargs: type("Result", (), {"points": [valid, _Point(id=2, payload=None), _Point(id=3, score="bad", payload={}), object()]})()})()
    store._client_override = client
    assert store.search([0.1, 0.2, 0.3]) == [valid]


@pytest.mark.parametrize("error", [ConnectionError("qdrant down"), TimeoutError("qdrant timeout")])
def test_qdrant_connection_failures_are_dependency_errors(error):
    store = QdrantStore(collection_name=f"test_qdrant_{uuid.uuid4().hex[:8]}", vector_size=3)
    client = type(
        "Client",
        (),
        {
            "query_points": lambda self, **kwargs: (_ for _ in ()).throw(error),
        },
    )()
    store._client_override = client

    with pytest.raises(RetrievalError) as raised:
        store.search([0.1, 0.2, 0.3])

    assert raised.value.error_code == "VECTOR_STORE_UNAVAILABLE"
    assert "qdrant" not in raised.value.message.lower()
