"""Regression tests for the document service fixes.

1. ``DocumentService`` is constructed per request, and eagerly building the
   Qdrant-backed vector store and retrieval engine cost ~8s per request
   (two ``QdrantStore`` constructions, each verifying the collection over the
   network). Read-only calls such as ``GET /documents`` only read record JSON
   from disk, so those collaborators are now created on first use.

2. ``delete_document`` passed a bare ``owner_id`` (i.e. ``None``) to
   ``refresh_engine`` while every other call site used
   ``owner_id or "anonymous"``. ``QdrantStore._combined_filter`` requires a
   non-null tenant, so the post-delete engine refresh could not scope its
   scroll and retrieval returned nothing until the process restarted.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.document_service import DocumentService


@pytest.fixture()
def service() -> DocumentService:
    from app.core.config import get_settings

    return DocumentService(get_settings())


class TestLazyCollaborators:
    def test_construction_does_not_build_vector_store(
        self,
        service: DocumentService,
    ) -> None:
        assert service._store is None
        assert service._engine is None

    def test_construction_is_cheap(self, service: DocumentService) -> None:
        """Construction must not perform the ~8s Qdrant round-trips."""
        import time

        from app.core.config import get_settings

        started = time.perf_counter()
        DocumentService(get_settings())
        elapsed = time.perf_counter() - started

        # Generous ceiling: the old eager path needed >8s per instance.
        assert elapsed < 1.0, f"construction took {elapsed:.2f}s"

    def test_list_documents_needs_no_vector_store(
        self,
        service: DocumentService,
    ) -> None:
        result = service.list_documents()

        assert set(result) == {"documents", "total"}
        # Still untouched - a read-only listing must not build it.
        assert service._store is None

    def test_vector_store_is_cached_after_first_use(
        self,
        service: DocumentService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        built = []

        class _Store:
            def __init__(self, *args, **kwargs):
                built.append(1)

        monkeypatch.setattr(
            "app.services.document_service.QdrantStore",
            _Store,
        )
        first = service._vector_store
        second = service._vector_store

        assert first is second
        assert len(built) == 1

    def test_retrieval_engine_is_cached_after_first_use(self) -> None:
        from app.core.config import get_settings

        service = DocumentService(get_settings())

        assert service._retrieval_engine is service._retrieval_engine


class TestDeleteOwnerScoping:
    def test_delete_refreshes_engine_with_anonymous_namespace(
        self,
        service: DocumentService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        refreshed: list[str | None] = []
        service.refresh_engine = lambda owner_id=None: refreshed.append(owner_id)  # type: ignore[method-assign]

        record = {"document_id": "doc-1", "owner_id": None}
        service._load_owned_record = MagicMock(return_value=record)  # type: ignore[method-assign]
        service._store = MagicMock()  # type: ignore[assignment]
        service._record_path = MagicMock(return_value="doc-1.json")  # type: ignore[method-assign]
        # Use monkeypatch so the shared FileManager is restored afterwards.
        monkeypatch.setattr(
            "app.services.document_service.FileManager.delete",
            MagicMock(),
        )

        service.delete_document("doc-1", owner_id=None)

        assert refreshed == ["anonymous"], (
            "delete must refresh the engine in the same owner namespace the "
            "store is scoped with, otherwise the post-delete refresh cannot "
            "filter by tenant and retrieval breaks until restart"
        )

    def test_delete_preserves_explicit_owner(
        self,
        service: DocumentService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        refreshed: list[str | None] = []
        service.refresh_engine = lambda owner_id=None: refreshed.append(owner_id)  # type: ignore[method-assign]
        service._load_owned_record = MagicMock(  # type: ignore[method-assign]
            return_value={"document_id": "doc-1", "owner_id": "u-1"}
        )
        service._store = MagicMock()  # type: ignore[assignment]
        service._record_path = MagicMock(return_value="doc-1.json")  # type: ignore[method-assign]
        # Use monkeypatch so the shared FileManager is restored afterwards.
        monkeypatch.setattr(
            "app.services.document_service.FileManager.delete",
            MagicMock(),
        )

        service.delete_document("doc-1", owner_id="u-1")

        assert refreshed == ["u-1"]


class TestRerankerCache:
    def test_reranker_is_process_wide(self) -> None:
        from app.retrieval.reranker import get_reranker

        assert get_reranker() is get_reranker()
