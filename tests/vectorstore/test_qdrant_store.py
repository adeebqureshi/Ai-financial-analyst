import uuid
from unittest.mock import Mock

import pytest
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.core.exceptions import RetrievalError
from app.vectorstore.qdrant_store import QdrantStore


def _store() -> QdrantStore:
    return QdrantStore(
        collection_name=f"test_qdrant_{uuid.uuid4().hex[:8]}",
        vector_size=3,
    )


def _assert_tenant_condition(query_filter, tenant_id):
    assert isinstance(query_filter, Filter)
    assert FieldCondition(
        key="tenant_id",
        match=MatchValue(value=tenant_id),
    ) in query_filter.must


def test_upsert_and_tenant_search():
    store = _store()
    store.upsert(
        ids=[1, 2],
        vectors=[[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]],
        payloads=[
            {"tenant_id": "tenant-a", "ticker": "AAPL"},
            {"tenant_id": "tenant-b", "ticker": "AAPL"},
        ],
    )

    tenant_a = store.search([0.1, 0.2, 0.3], limit=5, owner_id="tenant-a")
    tenant_b = store.search([0.1, 0.2, 0.3], limit=5, owner_id="tenant-b")

    assert [point.payload["tenant_id"] for point in tenant_a] == ["tenant-a"]
    assert [point.payload["tenant_id"] for point in tenant_b] == ["tenant-b"]


def test_document_filter_combines_with_tenant_filter_and_delete_is_tenant_scoped():
    store = _store()
    store.upsert(
        ids=[101, 202],
        vectors=[[0.1, 0.2, 0.3], [0.3, 0.2, 0.1]],
        payloads=[
            {"tenant_id": "tenant-a", "document_id": "a", "text": "apple"},
            {"tenant_id": "tenant-b", "document_id": "a", "text": "apple"},
        ],
    )
    scoped = store.search(
        [0.1, 0.2, 0.3],
        limit=5,
        document_id="a",
        owner_id="tenant-a",
    )
    assert len(scoped) == 1
    assert scoped[0].payload["tenant_id"] == "tenant-a"
    store.delete_by_document_id("a", owner_id="tenant-a")
    remaining = store.get_all(owner_id="tenant-b")
    assert len(remaining) == 1
    assert remaining[0].payload["tenant_id"] == "tenant-b"


class _Point:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_search_sends_exact_native_tenant_filter_to_query_points():
    store = _store()
    client = Mock()
    client.query_points.return_value = type("Result", (), {"points": []})()
    store._client_override = client

    store.search([0.1, 0.2, 0.3], owner_id="tenant-a", document_id="doc-a")

    query_filter = client.query_points.call_args.kwargs["query_filter"]
    _assert_tenant_condition(query_filter, "tenant-a")
    assert FieldCondition(
        key="document_id",
        match=MatchValue(value="doc-a"),
    ) in query_filter.must


def test_get_all_sends_exact_native_tenant_filter_to_scroll():
    store = _store()
    client = Mock()
    client.scroll.return_value = ([], None)
    store._client_override = client

    store.get_all(owner_id="tenant-b")

    scroll_filter = client.scroll.call_args.kwargs["scroll_filter"]
    _assert_tenant_condition(scroll_filter, "tenant-b")


@pytest.mark.parametrize("operation", ["search", "get_all"])
def test_missing_tenant_fails_before_qdrant_client_call(operation):
    store = _store()
    client = Mock()
    store._client_override = client

    with pytest.raises(RetrievalError) as raised:
        if operation == "search":
            store.search([0.1, 0.2, 0.3], owner_id=None)
        else:
            store.get_all(owner_id=None)

    assert raised.value.error_code == "TENANT_REQUIRED"
    client.query_points.assert_not_called()
    client.scroll.assert_not_called()


def test_search_filters_malformed_points():
    store = _store()
    valid = _Point(id=1, score=0.8, payload={"text": "valid", "chunk_id": "a:0"})
    client = Mock()
    client.query_points.return_value = type("Result", (), {"points": [valid, _Point(id=2, payload=None), _Point(id=3, score="bad", payload={}), object()]})()
    store._client_override = client
    assert store.search([0.1, 0.2, 0.3], owner_id="tenant-a") == [valid]


@pytest.mark.parametrize("error", [ConnectionError("qdrant down"), TimeoutError("qdrant timeout")])
def test_qdrant_connection_failures_are_dependency_errors(error):
    store = _store()
    client = Mock()
    client.query_points.side_effect = error
    store._client_override = client

    with pytest.raises(RetrievalError) as raised:
        store.search([0.1, 0.2, 0.3], owner_id="tenant-a")

    assert raised.value.error_code == "VECTOR_STORE_UNAVAILABLE"
    assert "qdrant" not in raised.value.message.lower()

