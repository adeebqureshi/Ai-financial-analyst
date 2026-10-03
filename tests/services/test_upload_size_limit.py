"""Regression tests for bounded upload reads.

Background
----------
``upload()`` and ``upload_background()`` previously called
``file.file.read()`` with no argument, which buffers the **entire** upload in
memory *before* ``_validate_pdf`` applies the ``_MAX_FILE_BYTES`` limit. The
limit therefore did not actually bound memory use — a single oversized request
could exhaust the process heap before being rejected.

These tests assert the two properties that matter: the read is bounded to the
limit, and an oversized payload is still rejected with the documented error.

The limit is monkeypatched to a tiny value so the test stays fast and
deterministic; the production value (100 MB) is never allocated.
"""

from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.services import document_service as document_service_module
from app.services.document_service import DocumentService


class RecordingStream:
    """A file-like object that records how many bytes were requested."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self.requested_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.requested_sizes.append(size)
        if size is None or size < 0:
            return self._payload
        return self._payload[:size]


class FakeUploadFile:
    def __init__(self, filename: str, payload: bytes) -> None:
        self.filename = filename
        self.file = RecordingStream(payload)


@pytest.fixture
def tiny_limit(monkeypatch):
    """Shrink the cap so the oversized case does not allocate 100 MB."""
    monkeypatch.setattr(document_service_module, "_MAX_FILE_BYTES", 64)
    return 64


def _service() -> DocumentService:
    """A service instance without running the heavyweight constructor.

    Both upload paths validate the payload before touching any other attribute,
    so the validation and read-bounding logic can be exercised in isolation.
    """
    return object.__new__(DocumentService)


def _pdf_bytes(size: int) -> bytes:
    body = b"%PDF-1.4\n" + b"A" * size
    return body.ljust(size, b"A")


class TestBoundedUploadRead:
    def test_oversized_upload_is_rejected(self, tiny_limit) -> None:
        service = _service()
        upload_file = FakeUploadFile("big.pdf", _pdf_bytes(4096))

        with pytest.raises(ValidationError) as excinfo:
            service.upload(upload_file)

        assert excinfo.value.error_code == "DOC_VAL_004"

    def test_read_is_bounded_to_limit_plus_one(self, tiny_limit) -> None:
        """The whole point of the fix: never buffer more than limit + 1 bytes."""
        service = _service()
        upload_file = FakeUploadFile("big.pdf", _pdf_bytes(4096))

        with pytest.raises(ValidationError):
            service.upload(upload_file)

        assert upload_file.file.requested_sizes == [tiny_limit + 1]
        # A bare read() would have recorded -1 (unbounded).
        assert -1 not in upload_file.file.requested_sizes

    def test_background_upload_rejects_oversized_payload(self, tiny_limit) -> None:
        service = _service()
        upload_file = FakeUploadFile("big.pdf", _pdf_bytes(4096))

        with pytest.raises(ValidationError) as excinfo:
            service.upload_background(upload_file)

        assert excinfo.value.error_code == "DOC_VAL_004"
        assert upload_file.file.requested_sizes == [tiny_limit + 1]

    def test_oversized_payload_is_truncated_to_the_bound(self, tiny_limit) -> None:
        """A large stream yields only limit+1 bytes, so memory stays bounded."""
        service = _service()
        # 10 MB offered; the read must only pull limit + 1 bytes out of it.
        upload_file = FakeUploadFile("big.pdf", _pdf_bytes(10 * 1024 * 1024))

        with pytest.raises(ValidationError):
            service.upload(upload_file)

        assert len(upload_file.file._payload) > tiny_limit
        assert upload_file.file.requested_sizes == [tiny_limit + 1]

    def test_non_pdf_is_rejected_before_size_check(self, tiny_limit) -> None:
        """Magic-byte validation still applies within the size bound."""
        service = _service()
        upload_file = FakeUploadFile("notes.txt", b"NOT-A-PDF" + b"B" * 200)

        with pytest.raises(ValidationError) as excinfo:
            service.upload(upload_file)

        assert excinfo.value.error_code == "DOC_VAL_002"

    def test_extension_without_pdf_magic_is_rejected(self, tiny_limit) -> None:
        service = _service()
        upload_file = FakeUploadFile("fake.pdf", b"just text, no pdf header")

        with pytest.raises(ValidationError) as excinfo:
            service.upload(upload_file)

        assert excinfo.value.error_code == "DOC_VAL_005"