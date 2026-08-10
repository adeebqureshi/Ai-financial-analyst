"""
Chat Service

This module contains the business logic for the conversational AI chat
endpoint. It uses the existing ``OpenAIClient`` for LLM generation and
grounds answers in retrieved document context with source citations.

Design Decisions:
    - **Document-first grounding**: Every message is first routed through the
      existing retrieval engine (optionally scoped to one uploaded document).
      Retrieved chunks are passed to the LLM together with their source
      metadata so answers can cite filename + page.
    - **No fabrication**: When retrieval returns no useful context the prompt
      instructs the model to say the answer could not be found rather than
      inventing content or page numbers.
    - **Existing LLM preserved**: Generation continues to go through
      ``OpenAIClient`` — no new LLM system is introduced.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.llm.models import LLMRequest
from app.llm.openai_client import OpenAIClient
from app.retrieval.models import RetrievedChunk
from app.schemas.responses import ChatResponseData, DocumentCitation
from app.services.document_service import DocumentService

logger = get_logger(__name__)

_NOT_FOUND_MESSAGE = (
    "I couldn't find sufficient information about that in the uploaded documents."
)


class ChatService:
    """
    Service for conversational AI chat grounded in uploaded documents.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

        self._client = OpenAIClient()

        self._documents = DocumentService(settings)

    def chat(self, request) -> ChatResponseData:
        """
        Send a chat message and get a grounded AI response with citations.

        Args:
            request: The validated chat request.

        Returns:
            A ``ChatResponseData`` with the assistant reply and sources.
        """
        context = self._documents.retrieve(
            query=request.message,
            limit=self._settings.vector_top_k,
            document_id=request.document_id,
        )

        sources = _build_citations(context.chunks)

        context_text = _build_context_text(context.chunks)

        prompt = _build_prompt(
            question=request.message,
            context_text=context_text,
            ticker=request.ticker,
        )

        llm_response = self._client.generate(LLMRequest(prompt=prompt))

        return ChatResponseData(
            message=llm_response.text,
            ticker=request.ticker,
            model=getattr(llm_response, "model", None),
            sources=sources,
        )


def _build_context_text(chunks: list[RetrievedChunk]) -> str:
    """
    Render retrieved chunks with page/source metadata for the LLM.
    """
    blocks: list[str] = []

    for chunk in chunks:
        location = []

        if chunk.filename:
            location.append(chunk.filename)

        if chunk.page is not None:
            location.append(f"page {chunk.page}")

        header = (
            f"[{', '.join(location)}]"
            if location
            else "[source]"
        )

        blocks.append(f"{header}\n{chunk.text}")

    return "\n\n".join(blocks)


def _build_citations(chunks: list[RetrievedChunk]) -> list[DocumentCitation]:
    """
    Deduplicate chunk metadata into stable source citations.
    """
    citations: list[DocumentCitation] = []

    seen: set[tuple[str, int | None]] = set()

    for chunk in chunks:
        if not chunk.document_id:
            continue

        key = (chunk.document_id, chunk.page)

        if key in seen:
            continue

        seen.add(key)

        citations.append(
            DocumentCitation(
                document_id=chunk.document_id,
                filename=chunk.filename or "Unknown document",
                page=chunk.page,
                chunk_id=chunk.chunk_id,
                score=chunk.score or 0.0,
            )
        )

    return citations


def _build_prompt(
    question: str,
    context_text: str,
    ticker: str | None,
) -> str:
    """
    Build a grounded RAG prompt for the existing LLM client.
    """
    if not context_text:
        return (
            "You are a financial document analyst. You answer questions using "
            "only information found in uploaded financial documents.\n\n"
            f"Question: {question}\n\n"
            f"If you cannot answer the question because no relevant document "
            f"context is available, respond exactly with: "
            f'"{_NOT_FOUND_MESSAGE}"\n'
            "Do NOT make up information, and do NOT invent page numbers or sources."
        )

    ticker_line = f"\nTicker context: {ticker}" if ticker else ""

    return (
        "You are a financial document analyst. Answer the question using ONLY "
        "the document context provided below.\n"
        "Each context block is labelled with its source filename and page.\n"
        "For every claim you make, cite the source and page, e.g. "
        '"According to <filename> (page <N>), ...".\n'
        "If the context does not contain the answer, respond exactly with: "
        f'"{_NOT_FOUND_MESSAGE}"\n'
        "Do NOT fabricate information, page numbers, or sources."
        f"{ticker_line}\n\n"
        f"Document context:\n{context_text}\n\n"
        f"Question: {question}"
    )
