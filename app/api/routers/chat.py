"""
Chat Router

This module defines the conversational AI endpoint (``POST /chat``).

Design Decisions:
    - **No business logic in route**: The route handler delegates entirely
      to ``ChatService.chat()``.
    - **Dependency injection**: ``ChatService`` is injected via
      ``Depends(get_chat_service)``, making it overridable in tests.
    - **Standard response format**: Returns ``APIResponse[ChatResponseData]``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_chat_service
from app.schemas.analysis import ChatRequest
from app.schemas.base import APIResponse
from app.schemas.responses import ChatResponseData
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=APIResponse[ChatResponseData],
    summary="Chat with the AI analyst",
    description="Sends a message to the LLM-powered financial analyst and returns a response.",
)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> APIResponse[ChatResponseData]:
    """
    Chat endpoint.

    Args:
        request: The validated chat request.
        service: Injected ``ChatService`` instance.

    Returns:
        An ``APIResponse`` containing the assistant reply.
    """
    result = service.chat(request)

    return APIResponse.success_response(
        message="Chat response generated",
        data=result,
    )