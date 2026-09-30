"""Regression tests for the document rate-limit bucket.

Background
----------
All four ``/documents`` routes used to share a single ``ratelimit:documents``
bucket (10/min, 100/hour, keyed by IP). The cheap, automatically polled
read-only routes (``GET /documents``) exhausted the hourly quota, which then
blocked the expensive ``POST /documents/upload`` with ``429`` and
``Retry-After: 3600`` — so a legitimate upload failed even though the user had
never uploaded anything.

These tests pin the intended semantics:

* reads are still rate limited (existing policy is preserved),
* reads have their **own** bucket and therefore never consume upload quota,
* uploads keep their own enforced quota,
* ``Retry-After`` is only produced when a limit is genuinely exceeded,
* state is isolated per user/IP and windows expire correctly.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import reset_rate_limits_for_testing
from app.api.dependencies.services import get_document_service
from app.api.rate_limiter import (
    LocalMemoryBackend,
    get_endpoint_config,
    get_rate_limiter,
    reset_rate_limiter,
)
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.config import Settings, get_settings
from app.main import app

client = TestClient(app)

PDF_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"


def make_settings(**overrides: object) -> Settings:
    return get_settings().model_copy(update=overrides)


def make_user(user_id: str = "doc-user-1") -> User:
    return User(
        id=user_id,
        email=f"{user_id}@example.com",
        hashed_password="hash",
        is_active=True,
    )


def install(
    settings: Settings,
    user: User | None,
    service: object,
) -> None:
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_document_service] = lambda: service


def document_service_stub() -> MagicMock:
    service = MagicMock()
    service.list_documents.return_value = {"documents": [], "total": 0}
    service.upload.return_value = {
        "document_id": "doc-1",
        "filename": "sample.pdf",
        "pages": 1,
        "chunks": 0,
        "tables": 0,
        "parser_used": "pymupdf",
        "status": "indexed",
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    return service


@pytest.fixture(autouse=True)
def _clean_rate_limits():
    reset_rate_limits_for_testing()
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()
    reset_rate_limiter()


def upload(client_: TestClient) -> object:
    return client_.post(
        "/documents/upload",
        files={"file": ("sample.pdf", PDF_BYTES, "application/pdf")},
    )


class TestDocumentRateLimitBuckets:
    def test_read_and_upload_use_separate_buckets(self) -> None:
        settings = make_settings(rate_limit_enabled=True)
        reads = get_endpoint_config("documents", settings)
        writes = get_endpoint_config("documents_upload", settings)

        assert reads.key_prefix != writes.key_prefix
        # The upload quota is not weakened by the split.
        assert writes.requests_per_minute == settings.rate_limit_documents_per_minute
        assert writes.requests_per_hour == settings.rate_limit_documents_per_hour

    def test_get_documents_does_not_return_429_on_first_request(self) -> None:
        settings = make_settings(rate_limit_enabled=True, auth_enabled=True)
        install(settings, make_user(), document_service_stub())

        response = client.get("/documents")

        assert response.status_code == 200, response.text

    def test_reads_do_not_consume_the_upload_quota(self) -> None:
        """The regression: reads must not exhaust the bucket uploads share."""
        settings = make_settings(rate_limit_enabled=True, auth_enabled=True)
        install(settings, make_user(), document_service_stub())

        for _ in range(settings.rate_limit_documents_per_minute + 5):
            client.get("/documents")

        # Reads are now blocked, proving the read quota is full...
        assert client.get("/documents").status_code == 429

        # ...but a legitimate first upload is still permitted.
        response = upload(client)
        assert response.status_code == 200, response.text

    def test_first_upload_is_accepted_before_the_quota_is_reached(self) -> None:
        settings = make_settings(rate_limit_enabled=True, auth_enabled=True)
        install(settings, make_user(), document_service_stub())

        response = upload(client)

        assert response.status_code == 200, response.text
        assert response.json()["data"]["document_id"] == "doc-1"

    def test_upload_limit_is_still_enforced(self) -> None:
        settings = make_settings(rate_limit_enabled=True, auth_enabled=True)
        install(settings, make_user(), document_service_stub())

        for i in range(settings.rate_limit_documents_per_minute):
            response = upload(client)
            assert response.status_code == 200, f"upload {i}: {response.text}"

        blocked = upload(client)
        assert blocked.status_code == 429
        assert int(blocked.headers["Retry-After"]) > 0

    def test_retry_after_only_present_when_limit_exceeded(self) -> None:
        settings = make_settings(rate_limit_enabled=True, auth_enabled=True)
        install(settings, make_user(), document_service_stub())

        allowed = upload(client)
        assert allowed.status_code == 200
        assert "Retry-After" not in allowed.headers

        for _ in range(settings.rate_limit_documents_per_minute):
            client.post(
                "/documents/upload",
                files={"file": ("s.pdf", PDF_BYTES, "application/pdf")},
            )

        blocked = upload(client)
        assert blocked.status_code == 429
        assert int(blocked.headers["Retry-After"]) > 0

    def test_rate_limit_state_is_isolated_between_users(self) -> None:
        settings = make_settings(rate_limit_enabled=True, auth_enabled=True)
        service = document_service_stub()
        install(settings, make_user("noisy-user"), service)

        for _ in range(settings.rate_limit_documents_per_minute + 1):
            client.get("/documents")
        assert client.get("/documents").status_code == 429

        # A different authenticated user must not be affected.
        install(settings, make_user("quiet-user"), document_service_stub())
        assert client.get("/documents").status_code == 200
        assert upload(client).status_code == 200

    def test_limits_can_be_disabled_explicitly(self) -> None:
        """The limiter is configurable, not hard-wired on."""
        settings = make_settings(rate_limit_enabled=False, auth_enabled=True)
        install(settings, make_user(), document_service_stub())

        for _ in range(50):
            assert client.get("/documents").status_code == 200


class TestWindowExpiry:
    def test_expired_window_resets(self) -> None:
        backend = LocalMemoryBackend()
        assert backend.increment("k", 60) == 1
        assert backend.increment("k", 60) == 2
        # Simulate the window having elapsed.
        backend._counters["k"] = (2, 0.0)
        assert backend.get("k") == 0
        assert backend.increment("k", 60) == 1

    def test_expired_key_is_reclaimed_by_cleanup(self) -> None:
        backend = LocalMemoryBackend()
        backend.increment("gone", 60)
        backend._counters["gone"] = (1, 0.0)
        backend._last_cleanup = 0.0  # force the cleanup pass
        backend._maybe_cleanup()
        assert "gone" not in backend._counters
