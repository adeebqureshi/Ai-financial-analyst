"""
Lightweight background-job registry.

A deliberately small, file-backed job store for long-running request work
(currently PDF ingestion). Jobs have a simple lifecycle::

    pending -> running -> completed
                       \\-> failed

Jobs are persisted as JSON under ``<metadata>/jobs`` so their state survives
process restarts; any job found in ``pending``/``running`` at startup is
marked ``failed`` with an "interrupted by restart" error so no work is ever
silently orphaned. Execution uses an in-process, single-worker
``ThreadPoolExecutor`` — heavy work is bounded to one at a time and never
blocks the event loop. This is intentionally *not* Celery/Kafka: for a
college-project scale deployment a single worker with durable state is
simpler to operate and debug.
"""

from __future__ import annotations

import json
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from app.core.logging import get_logger
from app.infrastructure.request_id import bind_request_id

logger = get_logger(__name__)

_TERMINAL_STATES = {"completed", "failed"}

_JOB_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _safe_message(exc: Exception) -> str:
    """Return a client-safe one-line error message."""
    raw = str(exc).strip()

    message = raw.splitlines()[0] if raw else "Unknown error."

    return message[:300]


class JobStore:
    """
    JSON-backed job registry with an in-process single-worker executor.
    """

    def __init__(self, jobs_dir: Path) -> None:
        self._jobs_dir = jobs_dir

        jobs_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()

        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="bg-job",
        )

        self._recover_orphans()

    # ── Persistence ───────────────────────────────────────────────────────

    def _job_path(self, job_id: str) -> Path:
        return self._jobs_dir / f"{job_id}.json"

    def _save(self, job: dict[str, Any]) -> None:
        tmp = self._job_path(job["job_id"]).with_suffix(".tmp")

        tmp.write_text(json.dumps(job, indent=2), encoding="utf-8")

        tmp.replace(self._job_path(job["job_id"]))

    def _read(self, job_id: str) -> dict[str, Any] | None:
        path = self._job_path(job_id)

        if not path.exists():
            return None

        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # pragma: no cover - defensive
            return None
    # ── Lifecycle ─────────────────────────────────────────────────────────

    def _recover_orphans(self) -> None:
        """
        Mark non-terminal jobs from a previous process as failed.

        Without this, an interrupted ingestion would stay ``pending``
        forever — the user would poll a job that can never finish.
        """
        for path in self._jobs_dir.glob("*.json"):
            try:
                job = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to load job record %s: %s", path, exc)

                continue

            if job.get("status") not in _TERMINAL_STATES:
                job["status"] = "failed"

                job["error"] = "Job was interrupted by a server restart."

                job["finished_at"] = _now_iso()

                self._save(job)

    def create_job(
        self,
        job_type: str,
        owner_id: str | None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register a new ``pending`` job and return its record."""
        job: dict[str, Any] = {
            "job_id": uuid.uuid4().hex,
            "type": job_type,
            "status": "pending",
            "owner_id": owner_id,
            "payload": payload or {},
            "error": None,
            "created_at": _now_iso(),
            "started_at": None,
            "finished_at": None,
        }

        with self._lock:
            self._save(job)

        return job

    def get_job(
        self,
        job_id: str,
        owner_id: str | None,
    ) -> dict[str, Any] | None:
        """
        Return the job record when it exists and is owned by ``owner_id``.

        Ownership follows the same convention as the document library:
        ``owner_id=None`` sees only anonymous jobs; an authenticated caller
        sees only their own. Foreign or malformed ids return ``None``.
        """
        if not job_id or not _JOB_ID_PATTERN.fullmatch(job_id):
            return None

        job = self._read(job_id)

        if job is None:
            return None

        if job.get("owner_id") != owner_id:
            # Conceal foreign jobs rather than revealing their existence.
            return None

        return job

    def submit(self, job_id: str, fn: Callable[[], Any]) -> None:
        """
        Run ``fn`` on the background worker, transitioning job state.

        ``fn`` performs the actual work; state transitions and error capture
        are handled here so callers cannot forget them.
        """
        self._transition(job_id, "running")

        logger.info("Background job started: job_id=%s", job_id)

        def _run() -> None:
            # Background threads run outside any HTTP request, so bind the
            # job ID as the correlation ID for every log record emitted by
            # the job (and anything it calls) — see app.core.logging.
            bind_request_id(job_id)

            start = time.perf_counter()

            try:
                fn()

                self._transition(job_id, "completed")

                logger.info(
                    "Background job completed: job_id=%s duration_ms=%.0f",
                    job_id,
                    (time.perf_counter() - start) * 1000,
                )
            except Exception as exc:
                logger.exception(
                    "Background job failed: job_id=%s duration_ms=%.0f "
                    "error_type=%s",
                    job_id,
                    (time.perf_counter() - start) * 1000,
                    exc.__class__.__name__,
                )

                with self._lock:
                    job = self._read(job_id) or {}

                    job["status"] = "failed"

                    # Never leak internal exception details to the client —
                    # a concise, single-line message only.
                    job["error"] = _safe_message(exc)

                    job["finished_at"] = _now_iso()

                    self._save(job)

        self._executor.submit(_run)

    # ── Internals ─────────────────────────────────────────────────────────

    def _transition(self, job_id: str, status: str) -> None:
        with self._lock:
            job = self._read(job_id)

            if job is None:
                return

            job["status"] = status

            if status == "running":
                job["started_at"] = _now_iso()
            elif status == "completed":
                job["finished_at"] = _now_iso()

            self._save(job)