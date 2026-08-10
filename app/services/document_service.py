"""
document_service.py

End-to-end financial document RAG pipeline.

Flow::

    PDF upload
        → validation
        → existing PDF loader (page-preserving)
        → page-aware chunking (existing chunker)
        → existing embedding service
        → existing Qdrant vector store
        → persistent document library (existing storage layer)
        → hybrid retrieval (dense + BM25 + RRF) + reranker

This service is the single orchestrator for the document lifecycle
(upload / list / delete) and document-scoped retrieval used by the chat
and search endpoints. It deliberately reuses the existing ingestion,
parsing, embedding and vector-store implementations rather than
duplicating any RAG architecture.
"""

from __future__ import annotations

import re
import tempfile
import uuid
import zlib
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.core.config import Settings
from app.core.exceptions import ParserError, ValidationError
from app.core.logging import get_logger
from app.embeddings.embedding_service import EmbeddingService
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.storage.file_manager import FileManager
from app.ingestion.storage.path_manager import PathManager
from app.parsers.chunker import Chunker
from app.retrieval.models import RetrievalContext
from app.retrieval.retrieval_engine import RetrievalEngine
from app.vectorstore.qdrant_store import QdrantStore

logger = get_logger(__name__)

_ALLOWED_MIME_TYPE = "application/pdf"

_MAX_FILE_BYTES = 100 * 1024 * 1024  # 100 MB

_FILING_TYPE_PATTERN = re.compile(
    r"(?:10-?K|10-?Q|8-?K|20-?F|S-?1|DEF\s*14A)",
    re.IGNORECASE,
)

_TICKER_PATTERN = re.compile(
    r"(?:^|[\s_\-.()])([A-Z]{1,5})(?:[\s_\-.()]|$)",
)


def _detect_filing_type(filename: str) -> str | None:
    """Best-effort extraction of an SEC form type from a filename."""
    match = _FILING_TYPE_PATTERN.search(filename)

    if match is None:
        return None

    return match.group(0).upper().replace(" ", "")


def _detect_ticker(filename: str) -> str | None:
    """Best-effort extraction of a ticker from a filename."""
    stem = Path(filename).stem

    for match in _TICKER_PATTERN.finditer(stem):
        token = match.group(1)

        if token in {
            "SEC",
            "PDF",
            "ANNUAL",
            "REPORT",
            "FILING",
            "FORM",
            "Q1",
            "Q2",
            "Q3",
            "Q4",
        }:
            continue

        return token

    return None


class DocumentService:
    """
    Orchestrates the financial document RAG lifecycle.
    """

    def __init__(
        self,
        settings: Settings,
        collection_name: str | None = None,
    ) -> None:
        self._settings = settings

        self._paths = PathManager()

        self._loader = PDFLoader()

        self._chunker = Chunker(
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )

        self._embedder = EmbeddingService()

        self._store = QdrantStore(
            collection_name=collection_name,
        )

        self._engine = RetrievalEngine()

    # ──────────────────────────────────────────────────────────────────
    # Persistent document library (existing storage layer)
    # ──────────────────────────────────────────────────────────────────

    def _library_dir(self) -> Path:
        return self._paths.get_metadata_path() / "documents"

    def _record_path(self, document_id: str) -> Path:
        return self._library_dir() / f"{document_id}.json"

    def _save_record(self, record: dict) -> None:
        FileManager.save_json(
            self._record_path(record["document_id"]),
            record,
        )

    def _load_record(self, document_id: str) -> dict | None:
        path = self._record_path(document_id)

        if not path.exists():
            return None

        return FileManager.load_json(path)

    # ──────────────────────────────────────────────────────────────────
    # Validation
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _validate_pdf(filename: str, content: bytes) -> None:
        if not filename:
            raise ValidationError(
                message="Uploaded file must have a filename.",
                error_code="DOC_VAL_001",
            )

        if not filename.lower().endswith(".pdf"):
            raise ValidationError(
                message="Only PDF documents are supported.",
                error_code="DOC_VAL_002",
                details={"filename": filename},
            )

        if not content:
            raise ValidationError(
                message="Uploaded file is empty.",
                error_code="DOC_VAL_003",
                details={"filename": filename},
            )

        if len(content) > _MAX_FILE_BYTES:
            raise ValidationError(
                message="Uploaded file exceeds the 100 MB size limit.",
                error_code="DOC_VAL_004",
                details={"filename": filename},
            )

        if not content.lstrip().startswith(b"%PDF"):
            raise ValidationError(
                message="Uploaded file is not a valid PDF document.",
                error_code="DOC_VAL_005",
                details={"filename": filename},
            )

    # ──────────────────────────────────────────────────────────────────
    # Upload / index
    # ──────────────────────────────────────────────────────────────────

    def upload(self, file: UploadFile) -> dict:
        """
        Parse, chunk, embed and index an uploaded PDF.

        Returns:
            A document record with ``document_id``, ``filename``,
            ``pages``, ``chunks`` and ``status``.
        """
        filename = Path(file.filename or "").name

        content = file.file.read()

        self._validate_pdf(filename, content)

        document_id = uuid.uuid4().hex

        tmp_path = self._write_temp(content)

        try:
            document = self._loader.load(tmp_path)
        except Exception as exc:
            raise ParserError(
                message=f"Failed to parse PDF: {exc}",
                error_code="DOC_PARSE_001",
                details={"filename": filename},
            ) from exc
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        if document.is_empty:
            raise ParserError(
                message="No text could be extracted from the PDF.",
                error_code="DOC_PARSE_002",
                details={"filename": filename},
            )

        pages = document.pages or [document.text]

        chunks = self._chunker.chunk_pages(pages)

        texts = [chunk.text for chunk in chunks]

        vectors = self._embedder.embed_documents(texts)

        filing_type = _detect_filing_type(filename)

        ticker = _detect_ticker(filename)

        ids: list[int] = []

        payloads: list[dict] = []

        for index, chunk in enumerate(chunks):
            chunk_id = f"{document_id}:{index:06d}"

            page = chunk.page

            ids.append(
                zlib.crc32(chunk_id.encode("utf-8"))
            )

            payloads.append(
                {
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_id": chunk_id,
                    "page": page,
                    "section": chunk.section or "Document",
                    "text": chunk.text,
                    "ticker": ticker or "",
                    "filing_type": filing_type or "PDF",
                    "source": f"{filename}:page-{page}",
                }
            )

        self._store.upsert(
            ids=ids,
            vectors=vectors,
            payloads=payloads,
        )

        record = {
            "document_id": document_id,
            "filename": filename,
            "pages": len(pages),
            "chunks": len(chunks),
            "status": "indexed",
            "created_at": datetime.now(UTC).isoformat(),
        }

        self._save_record(record)

        self.refresh_engine()

        logger.info(
            "Indexed document %s (%d pages, %d chunks)",
            document_id,
            len(pages),
            len(chunks),
        )

        return record

    @staticmethod
    def _write_temp(content: bytes) -> str:
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
        ) as tmp:
            tmp.write(content)
            return tmp.name

    # ──────────────────────────────────────────────────────────────────
    # Library
    # ──────────────────────────────────────────────────────────────────

    def list_documents(self) -> dict:
        records = self._list_records()

        return {
            "documents": records,
            "total": len(records),
        }

    def _list_records(self) -> list[dict]:
        directory = self._library_dir()

        if not directory.exists():
            return []

        records: list[dict] = []

        for path in sorted(directory.glob("*.json")):
            try:
                records.append(FileManager.load_json(path))
            except Exception as exc:
                logger.warning("Failed to load document record %s: %s", path, exc)

        records.sort(
            key=lambda record: record.get("created_at") or "",
            reverse=True,
        )

        return records

    def get_document(self, document_id: str) -> dict:
        record = self._load_record(document_id)

        if record is None:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_id}' was not found.",
            )

        return record

    def delete_document(self, document_id: str) -> dict:
        if self._load_record(document_id) is None:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_id}' was not found.",
            )

        self._store.delete_by_document_id(document_id)

        FileManager.delete(self._record_path(document_id))

        self.refresh_engine()

        logger.info("Deleted document %s", document_id)

        return {"document_id": document_id}

    # ──────────────────────────────────────────────────────────────────
    # Retrieval
    # ──────────────────────────────────────────────────────────────────

    def refresh_engine(self) -> None:
        """
        Rebuild BM25 + metadata indexes from the persistent vector store.
        """
        try:
            self._engine.refresh(self._store)
        except Exception as exc:
            logger.warning("Failed to refresh retrieval engine: %s", exc)

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        document_id: str | None = None,
    ) -> RetrievalContext:
        """
        Retrieve relevant chunks, optionally scoped to a single document.
        """
        self.refresh_engine()

        return self._engine.retrieve(
            query=query,
            limit=limit,
            document_id=document_id,
        )
