"""
models.py

Domain models for retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class RetrievedChunk:
    """
    One retrieved chunk returned by the retrieval engine.
    """

    id: str

    text: str

    score: float

    ticker: str

    filing_type: str

    filing_date: date | None

    section: str

    source: str

    document_id: str | None = None

    filename: str | None = None

    page: int | None = None

    chunk_id: str | None = None


@dataclass(slots=True)
class RetrievalContext:
    """
    Final context passed to the LLM.
    """

    query: str

    chunks: list[RetrievedChunk]

    retrieval_time_ms: float