from __future__ import annotations
from dataclasses import dataclass
from datetime import date
@dataclass(slots=True)
class RetrievedChunk:
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
    parser_used: str | None = None
    owner_id: str | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    transaction_time: date | None = None
@dataclass(slots=True)
class RetrievalContext:
    query: str
    chunks: list[RetrievedChunk]
    retrieval_time_ms: float