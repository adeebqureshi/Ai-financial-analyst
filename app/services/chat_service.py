"""
Chat Service

This module contains the business logic for the conversational AI chat
endpoint. It delegates to the existing ``OpenAIClient`` for LLM generation
and wraps the results in typed response DTOs.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.llm.models import LLMRequest
from app.llm.openai_client import OpenAIClient
from app.retrieval.retrieval_engine import RetrievalEngine
from app.schemas.analysis import ChatRequest
from app.schemas.responses import ChatResponseData

logger = get_logger(__name__)


class ChatService:
    """
    Service for conversational AI chat.

    Attributes:
        _settings: Application settings instance.
        _client: OpenAI LLM client.
        _retrieval: Retrieval engine for optional context.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = OpenAIClient()
        self._retrieval = RetrievalEngine()

    def chat(self, request: ChatRequest) -> ChatResponseData:
        """
        Send a chat message and get an AI response.

        Args:
            request: The validated chat request.

        Returns:
            A ``ChatResponseData`` with the assistant reply.
        """
        # If context is not provided, try to retrieve it
        context_text = request.context or ""
        if not context_text:
            try:
                retrieval_context = self._retrieval.retrieve(
                    query=request.message,
                    limit=3,
                )
                if retrieval_context.chunks:
                    context_text = " ".join(c.text for c in retrieval_context.chunks[:3])
            except Exception as exc:
                logger.debug("Chat context retrieval failed: %s", exc)

        # Build the prompt
        if context_text:
            prompt = f"Context:\n{context_text}\n\nQuestion: {request.message}"
        else:
            prompt = request.message

        # Generate response
        llm_response = self._client.generate(LLMRequest(prompt=prompt))

        return ChatResponseData(
            message=llm_response.text,
            ticker=request.ticker,
            model=getattr(llm_response, "model", None),
        )