from __future__ import annotations

import re
import tempfile
import threading
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile

# --- FIXED IMPORTS: No duplicates, no conflicting AuthenticationError ---
from app.auth.exceptions import AuthenticationError, AuthorizationError
from app.core.config import Settings
from app.core.exceptions import ParserError, ValidationError
from app.core.logging import get_logger
from app.embeddings.embedding_service import EmbeddingService
from app.ingestion.document_parser import UnifiedDocumentParser
from app.ingestion.storage.file_manager import FileManager
from app.ingestion.storage.path_manager import PathManager
from app.parsers.chunker import Chunker
from app.retrieval.models import RetrievalContext
from app.retrieval.retrieval_engine import RetrievalEngine
from app.services.job_store import JobStore
from app.vectorstore.qdrant_store import QdrantStore

_demo_vector_store = None


def _get_demo_vector_store():
    global _demo_vector_store
    if _demo_vector_store is None:
        from app.demo.fixtures.rag_fixtures import create_demo_vector_store

        _demo_vector_store = create_demo_vector_store()
    return _demo_vector_store


def _build_demo_retrieval_context(query: str, ticker: str | None, limit: int):
    from app.demo.fixtures.rag_fixtures import build_demo_retrieval_context

    return build_demo_retrieval_context(query, ticker, limit)


logger = get_logger(__name__)

# Serializes ownership check + delete so concurrent requests cannot both pass
# the check before either one removes the record (check-then-act race).
# Class-level because a new DocumentService instance is built per request.
_delete_lock = threading.Lock()

_ALLOWED_MIME_TYPE = "application/pdf"
_MAX_FILE_BYTES = 100 * 1024 * 1024
_FILING_TYPE_PATTERN = re.compile(
    r"(?:10-?K|10-?Q|8-?K|20-?F|S-?1|DEF\s*14A)",
    re.IGNORECASE,
)
_TICKER_PATTERN = re.compile(
    r"(?:^|[\s_\-.()])([A-Z]{1,5})(?:[\s_\-.()]|$)",
)
_DOCUMENT_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def _detect_filing_type(filename: str) -> str | None:
    match = _FILING_TYPE_PATTERN.search(filename)
    if match is None:
        return None
    return match.group(0).upper().replace(" ", "")


def _detect_ticker(filename: str) -> str | None:
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
    def __init__(
        self,
        settings: Settings,
        collection_name: str | None = None,
    ) -> None:
        self._settings = settings
        self._paths = PathManager()
        self._jobs = JobStore(self._paths.get_metadata_path() / "jobs")
        self._parser = UnifiedDocumentParser(
            api_key=settings.llama_parse_api_key_str,
        )
        self._chunker = Chunker(
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )
        self._embedder = EmbeddingService()
        if settings.is_demo_mode:
            self._store = _get_demo_vector_store()
        else:
            self._store = QdrantStore(
                collection_name=collection_name,
            )
        self._engine = RetrievalEngine()

    def _library_dir(self) -> Path:
        return self._paths.get_metadata_path() / "documents"

    def _record_path(self, document_id: str) -> Path:
        return self._library_dir() / f"{document_id}.json"

    @staticmethod
    def _is_valid_document_id(document_id: str) -> bool:
        return bool(_DOCUMENT_ID_PATTERN.fullmatch(document_id))

    @staticmethod
    def _not_found(document_id: str | None = None) -> HTTPException:
        return HTTPException(
            status_code=404,
            detail="Document was not found.",
        )

    def _save_record(self, record: dict) -> None:
        FileManager.save_json(
            self._record_path(record["document_id"]),
            record,
        )

    def _load_record(self, document_id: str) -> dict | None:
        if not self._is_valid_document_id(document_id):
            return None
        path = self._record_path(document_id)
        if not path.exists():
            return None
        try:
            return FileManager.load_json(path)
        except FileNotFoundError:
            # Deleted between exists() and open() by a concurrent request.
            return None

    @staticmethod
    def _is_owned(record: dict, owner_id: str | None) -> bool:
        """
        Check record ownership within a single anonymous/authenticated namespace.

        Anonymous records (owner None) are visible only to anonymous callers;
        authenticated records only to the matching user. Cross-namespace
        access (including authenticated users reaching legacy unowned
        records) is denied, preventing IDOR.
        """
        record_owner = record.get("owner_id")
        return str(record_owner or "") == str(owner_id or "") and str(owner_id or "") != "" or (
            record_owner is None and owner_id is None
        )

    def _load_owned_record(
        self,
        document_id: str,
        owner_id: str | None,
        *,
        conceal: bool = True,
    ) -> dict:
        record = self._load_record(document_id)
        if record is None:
            raise self._not_found(document_id)

        if not self._is_owned(record, owner_id):
            if conceal:
                raise self._not_found(document_id)
            if not owner_id:
                raise AuthorizationError("Authentication required to access this document.")
            raise AuthorizationError("You do not have access to this document.")

        return record

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

    def upload(
        self,
        file: UploadFile,
        owner_id: str | None = None,
    ) -> dict:
        filename = Path(file.filename or "").name
        content = file.file.read()
        self._validate_pdf(filename, content)
        document_id = uuid.uuid4().hex
        tmp_path = self._write_temp(content)
        try:
            return self._process_pdf(tmp_path, filename, document_id, owner_id)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def _process_pdf(
        self,
        pdf_path: str,
        filename: str,
        document_id: str,
        owner_id: str | None,
    ) -> dict:
        try:
            result = self._parser.parse(
                pdf_path,
                filename=filename,
            )
        except Exception as exc:
            raise ParserError(
                message=f"Failed to parse PDF: {exc}",
                error_code="DOC_PARSE_001",
                details={"filename": filename},
            ) from exc

        if result.is_empty:
            raise ParserError(
                message="No text could be extracted from the PDF.",
                error_code="DOC_PARSE_002",
                details={"filename": filename},
            )

        pages = result.pages or [result.text]
        chunks = self._chunker.chunk_pages(pages)
        texts = [chunk.text for chunk in chunks]
        vectors = self._embedder.embed_documents(texts)
        filing_type = _detect_filing_type(filename)
        ticker = _detect_ticker(filename)
        tables_by_page: dict[int, list[dict[str, object]]] = {}
        for table in result.tables:
            if table.source_page is None:
                continue
            tables_by_page.setdefault(table.source_page, []).append(
                table.to_dict()
            )

        ids: list[int] = []
        payloads: list[dict] = []
        transaction_time = datetime.now(UTC).date()
        for index, chunk in enumerate(chunks):
            chunk_id = f"{document_id}:{index:06d}"
            page = chunk.page
            ids.append(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))
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
                    "parser_used": result.parser_used,
                    "tables": tables_by_page.get(page, []),
                    "transaction_time": transaction_time.isoformat(),
                    "owner_id": owner_id or "anonymous",
                    "tenant_id": owner_id or "anonymous",
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
            "tables": len(result.tables),
            "parser_used": result.parser_used,
            "status": "indexed",
            "created_at": datetime.now(UTC).isoformat(),
            "owner_id": owner_id,
        }
        self._save_record(record)
        self.refresh_engine(owner_id or "anonymous")
        logger.info(
            "Indexed document %s (%d pages, %d chunks, %d tables, %s)",
            document_id,
            len(pages),
            len(chunks),
            len(result.tables),
            result.parser_used,
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

    def _staging_path(self, job_id: str) -> Path:
        staging_dir = self._paths.get_metadata_path() / "uploads"
        staging_dir.mkdir(parents=True, exist_ok=True)
        return staging_dir / f"{job_id}.pdf"

    def upload_background(
        self,
        file: UploadFile,
        owner_id: str | None = None,
    ) -> dict:
        filename = Path(file.filename or "").name
        content = file.file.read()
        self._validate_pdf(filename, content)
        document_id = uuid.uuid4().hex
        job = self._jobs.create_job(
            "document_ingestion",
            owner_id,
            payload={"document_id": document_id, "filename": filename},
        )
        job_id = job["job_id"]
        staging_path = self._staging_path(job_id)
        staging_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path.write_bytes(content)
        self._save_record(
            {
                "document_id": document_id,
                "filename": filename,
                "pages": 0,
                "chunks": 0,
                "tables": 0,
                "parser_used": None,
                "status": "pending",
                "job_id": job_id,
                "created_at": datetime.now(UTC).isoformat(),
                "owner_id": owner_id,
            }
        )
        self._jobs.submit(
            job_id,
            lambda: self._run_background_job(
                job_id,
                staging_path,
                filename,
                document_id,
                owner_id,
            ),
        )
        logger.info(
            "Queued background ingestion job %s for %s (%d bytes)",
            job_id,
            filename,
            len(content),
        )
        return {
            "document_id": document_id,
            "filename": filename,
            "job_id": job_id,
            "status": "pending",
        }

    def _run_background_job(
        self,
        job_id: str,
        staging_path: Path,
        filename: str,
        document_id: str,
        owner_id: str | None,
    ) -> None:
        try:
            self._process_pdf(str(staging_path), filename, document_id, owner_id)
        except Exception:
            record = self._load_record(document_id)
            if record is not None:
                record["status"] = "failed"
                self._save_record(record)
            raise
        finally:
            staging_path.unlink(missing_ok=True)

    def get_job(self, job_id: str, owner_id: str | None = None) -> dict | None:
        # JobStore enforces ownership itself: a job is only visible when its
        # stored owner_id matches the caller (None == anonymous namespace),
        # so cross-user access returns None and surfaces as a 404.
        return self._jobs.get_job(job_id, owner_id)

    def list_documents(self, owner_id: str | None = None) -> dict:
        """
        Lists documents scoped strictly to the provided owner namespace.

        Anonymous callers (owner None) see only anonymous records;
        authenticated callers see only their own records.
        """
        records = self._list_records()
        namespace = str(owner_id or "")
        records = [
            record
            for record in records
            if str(record.get("owner_id") or "") == namespace
        ]
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

    def get_document(
        self,
        document_id: str,
        owner_id: str | None = None,
    ) -> dict:
        return self._load_owned_record(document_id, owner_id)

    def delete_document(
        self,
        document_id: str,
        owner_id: str | None = None,
    ) -> dict:
        with _delete_lock:
            self._load_owned_record(document_id, owner_id)
            self._store.delete_by_document_id(
                document_id,
                owner_id=owner_id or "anonymous",
            )
            FileManager.delete(self._record_path(document_id))
            self.refresh_engine(owner_id)
        logger.info("Deleted document %s", document_id)
        return {"document_id": document_id}

    def refresh_engine(self, owner_id: str | None = None) -> None:
        try:
            self._engine.refresh(self._store, owner_id=owner_id)
        except Exception as exc:
            logger.warning("Failed to refresh retrieval engine: %s", exc)

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        document_id: str | None = None,
        as_of_date: date | None = None,
        owner_id: str | None = None,
    ) -> RetrievalContext:
        if self._settings.is_demo_mode:
            ticker = None
            if document_id and document_id.startswith("demo_"):
                parts = document_id.split("_")
                if len(parts) >= 2:
                    ticker = parts[1]
            return _build_demo_retrieval_context(query, ticker, limit)

        self.refresh_engine(owner_id or "anonymous")
        if document_id is not None:
            try:
                self._load_owned_record(document_id, owner_id)
            except HTTPException:
                return RetrievalContext(
                    query=query,
                    chunks=[],
                    retrieval_time_ms=0.0,
                )

        return self._engine.retrieve(
            query=query,
            limit=limit,
            document_id=document_id,
            as_of_date=as_of_date,
            owner_id=owner_id or "anonymous",
        )