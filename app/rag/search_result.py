"""
Search result model.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.rag.embedding import Embedding


@dataclass(slots=True)
class SearchResult:
    embedding: Embedding
    score: float