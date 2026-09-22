from __future__ import annotations
from datetime import date
from app.rag.temporal_metadata import TemporalMetadata
from app.retrieval.models import RetrievedChunk
class MetadataFilter:
    def filter(
        self,
        chunks: list[RetrievedChunk],
        ticker: str | None = None,
        filing_type: str | None = None,
        year: int | None = None,
        as_of_date: date | None = None,
    ) -> list[RetrievedChunk]:
        results = chunks
        if ticker is not None:
            results = [
                c
                for c in results
                if c.ticker == ticker
            ]
        if filing_type is not None:
            results = [
                c
                for c in results
                if c.filing_type == filing_type
            ]
        if year is not None:
            results = [
                c
                for c in results
                if c.filing_date
                and c.filing_date.year == year
            ]
        if as_of_date is not None:
            results = apply_temporal_filter(
                results,
                as_of_date,
            )
        return results
def apply_temporal_filter(
    chunks: list[RetrievedChunk],
    as_of_date: date,
) -> list[RetrievedChunk]:
    if not chunks:
        return chunks
    filtered: list[RetrievedChunk] = []
    for chunk in chunks:
        temporal = TemporalMetadata(
            valid_from=chunk.valid_from,
            valid_until=chunk.valid_until,
            transaction_time=chunk.transaction_time,
        )
        if temporal.is_valid_at(as_of_date):
            filtered.append(chunk)
    return filtered