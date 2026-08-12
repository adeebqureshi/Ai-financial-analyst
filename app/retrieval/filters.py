"""
filters.py

Metadata filtering for retrieved chunks.
"""

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
    """
    Exclude chunks that were not available/valid by ``as_of_date``.

    A chunk is retained only when its bitemporal metadata satisfies::

        transaction_time <= as_of_date
        AND valid_from     <= as_of_date
        AND (valid_until is None OR valid_until >= as_of_date)

    Missing metadata is handled conservatively for historical queries:

    - A missing ``transaction_time`` cannot prove the system knew the
      information by the query date, so the chunk is **excluded** to prevent
      look-ahead leakage.
    - A missing ``valid_from`` or ``valid_until`` is treated as unbounded
      (valid on both ends) since the transaction-time check is the primary
      guard against look-ahead bias.

    This function is side-effect free and never mutates the input chunks.
    """
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