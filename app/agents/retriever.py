"""
Retriever agent.
"""

from __future__ import annotations

from app.agents.retrieval_result import RetrievalResult
from app.rag.context_builder import ContextBuilder
from app.rag.embedding import Embedding
from app.rag.hybrid_retriever import HybridRetriever
from app.rag.search_result import SearchResult


class RetrieverAgent:
    """
    Retrieves relevant financial documents.
    """

    def __init__(self) -> None:

        self.retriever = HybridRetriever()

        self.builder = ContextBuilder()

    def retrieve(
        self,
        query: str,
        documents: list[Embedding],
    ) -> RetrievalResult:

        query_embedding = Embedding(
            text=query,
            vector=[1.0, 0.0],
        )

        results = self.retriever.search(
            query_embedding=query_embedding,
            documents=documents,
        )

        context = self.builder.build(results)

        return RetrievalResult(
            query=query,
            documents=context.text.split("\n\n"),
        )