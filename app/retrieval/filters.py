"""
filters.py

Metadata filtering for retrieved chunks.
"""

from __future__ import annotations

from app.retrieval.models import RetrievedChunk


class MetadataFilter:

    def filter(
        self,
        chunks: list[RetrievedChunk],
        ticker: str | None = None,
        filing_type: str | None = None,
        year: int | None = None,
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

        return results