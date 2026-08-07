"""
retriever.py

Retriever agent.
"""

from __future__ import annotations

from app.retrieval.retrieval_engine import RetrievalEngine


class RetrieverAgent:

    def __init__(self) -> None:

        self.engine = RetrievalEngine()

    def retrieve(
        self,
        query: str,
        limit: int = 5,
    ):

        return self.engine.retrieve(
            query=query,
            limit=limit,
        )