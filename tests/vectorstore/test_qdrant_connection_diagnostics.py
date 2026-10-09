"""Regression tests for the local-Qdrant connection failure.

The reported symptom was a gRPC ``UNAVAILABLE / 127.0.0.1:6334 / connection
refused`` warning at startup followed by "falling back to local resources".
The root cause was that the local Qdrant server was not running at all; the
configuration and the collection on disk were both intact. These tests lock in
the diagnostics that make that state distinguishable from a data problem.
"""

from contextlib import contextmanager
from unittest.mock import Mock, patch

import pytest

from app.core.exceptions import RetrievalError
from app.vectorstore import qdrant_store as qdrant_module
from app.vectorstore.qdrant_store import (
    QdrantStore,
    _DEFAULT_GRPC_PORT,
    _get_shared_client,
    _reset_shared_client_for_tests,
)


@pytest.fixture(autouse=True)
def _isolated_client():
    _reset_shared_client_for_tests()
    yield
    _reset_shared_client_for_tests()


def _store_with_client(client) -> QdrantStore:
    """Build a store pointed at an unreachable server.

    Construction normally performs the collection check itself, so it is
    bypassed here and re-run explicitly once the failing client is in place.
    """
    with patch.object(QdrantStore, "_ensure_collection"):
        store = QdrantStore(
            collection_name="financial_documents",
            vector_size=384,
            url="http://localhost:6333",
        )
    store._client_override = client
    return store


@contextmanager
def _captured_warnings():
    """Collect emitted warnings regardless of global logging configuration.

    Other tests call ``setup_logging(force=True)``, which detaches the shared
    logger from ``caplog``'s handler. Patching the module logger keeps these
    assertions stable regardless of test ordering.
    """
    messages: list[str] = []

    def _record(message, *args, **kwargs):
        messages.append(str(message) % args if args else str(message))

    with patch.object(qdrant_module.logger, "warning", _record):
        yield messages


def test_unreachable_server_reports_configured_endpoint_and_grpc_port():
    """A stopped server must be logged as unreachable, not as a data problem."""
    client = Mock()
    client.get_collections.side_effect = ConnectionRefusedError(
        "failed to connect to all addresses 127.0.0.1:6334"
    )
    with _captured_warnings() as messages:
        with pytest.raises(RetrievalError) as excinfo:
            _store_with_client(client)._ensure_collection()

    assert excinfo.value.error_code == "VECTOR_STORE_UNAVAILABLE"
    message = " ".join(messages)
    assert "unreachable" in message
    assert "http://localhost:6333" in message
    assert str(_DEFAULT_GRPC_PORT) in message
    assert "financial_documents" in message


def test_unreachable_server_log_never_leaks_api_key():
    client = Mock()
    client.get_collections.side_effect = ConnectionRefusedError("refused")
    with _captured_warnings() as messages:
        with pytest.raises(RetrievalError):
            _store_with_client(client)._ensure_collection()
    assert "super-secret-key" not in " ".join(messages)


def test_missing_url_logs_that_documents_are_not_searchable():
    """The in-memory substitution must be loud, never a silent empty store."""
    with patch("app.vectorstore.qdrant_store.QdrantClient") as client_cls:
        client_cls.return_value = Mock()
        with _captured_warnings() as messages:
            _get_shared_client(None, None)

    client_cls.assert_called_once_with(":memory:")
    assert "not searchable" in " ".join(messages).lower()