from datetime import date
from unittest.mock import MagicMock

from app.core.config import get_settings
from app.llm.models import LLMResponse
from app.retrieval.models import RetrievalContext, RetrievedChunk
from app.schemas.analysis import ChatRequest
from app.services.chat_service import _NOT_FOUND_MESSAGE, ChatService


def _chunk(
    text: str,
    document_id: str = "doc1",
    filename: str = "Apple 10-K.pdf",
    page: int = 42,
) -> RetrievedChunk:
    return RetrievedChunk(
        id=f"{document_id}:0",
        chunk_id=f"{document_id}:0",
        text=text,
        score=0.9,
        document_id=document_id,
        filename=filename,
        page=page,
        ticker="AAPL",
        filing_type="10-K",
        filing_date=date(2024, 10, 31),
        section="Risk Factors",
        source=f"{filename}:page-{page}",
    )


def _chat_service():
    settings = get_settings()

    service = ChatService(settings)

    service._client = MagicMock()

    service._documents = MagicMock()

    return service


def _context(chunks):
    return RetrievalContext(
        query="risk",
        chunks=chunks,
        retrieval_time_ms=10.0,
    )


def test_grounded_answer_returns_citations():
    service = _chat_service()

    chunk = _chunk("Apple faces supply chain concentration risk.")

    service._documents.retrieve.return_value = _context([chunk])

    service._client.generate.return_value = LLMResponse(
        text="According to Apple 10-K.pdf (page 42), Apple faces supply chain risk.",
        model="mock",
    )

    result = service.chat(
        ChatRequest(
            message="What are Apple's risks?",
            ticker="AAPL",
            document_id="doc1",
        )
    )

    assert "supply chain" in result.message

    assert len(result.sources) == 1

    source = result.sources[0]

    assert source.document_id == "doc1"

    assert source.filename == "Apple 10-K.pdf"

    assert source.page == 42

    # retrieval was scoped to the requested document
    service._documents.retrieve.assert_called_once_with(
        query="What are Apple's risks?",
        limit=service._settings.vector_top_k,
        document_id="doc1",
    )


def test_prompt_includes_source_metadata():
    service = _chat_service()

    chunk = _chunk("AI infrastructure spending grew.", page=63)

    service._documents.retrieve.return_value = _context([chunk])

    service._client.generate.return_value = LLMResponse(
        text="According to the report (page 63), spending grew.",
        model="mock",
    )

    service.chat(
        ChatRequest(
            message="What did management say about AI spending?",
            document_id="doc1",
        )
    )

    prompt = service._client.generate.call_args[0][0].prompt

    assert "Apple 10-K.pdf" in prompt

    assert "page 63" in prompt


def test_no_context_does_not_fabricate():
    service = _chat_service()

    service._documents.retrieve.return_value = _context([])

    service._client.generate.return_value = LLMResponse(
        text=_NOT_FOUND_MESSAGE,
        model="mock",
    )

    result = service.chat(
        ChatRequest(
            message="What was the 2015 CEO salary?",
        )
    )

    assert result.message == _NOT_FOUND_MESSAGE

    assert result.sources == []

    prompt = service._client.generate.call_args[0][0].prompt

    assert _NOT_FOUND_MESSAGE in prompt
