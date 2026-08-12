"""
Chat Router

This module defines the conversational AI endpoints:

- ``POST /chat``         — non-streaming chat response.
- ``POST /chat/stream``  — Server-Sent Events (SSE) streaming chat response.

Design Decisions:
    - **No business logic in route**: Route handlers delegate entirely to
      ``ChatService.chat()`` / ``ChatService.stream_chat()``.
    - **Dependency injection**: ``ChatService`` is injected via
      ``Depends(get_chat_service)``, making it overridable in tests.
    - **Standard response format**: Returns ``APIResponse[ChatResponseData]``.
    - **SSE for streaming**: ``/chat/stream`` returns a ``StreamingResponse``
      with ``text/event-stream``; each SSE frame is self-contained so a client
      can render tokens as they arrive.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

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


@router.post(
    "/stream",
    summary="Stream a chat response",
    description=(
        "Sends a message to the LLM-powered financial analyst and streams the "
        "answer back as Server-Sent Events (SSE). Emits ``plan``, ``token``, "
        "``done`` and ``error`` events so clients can render tokens live."
    ),
)
async def chat_stream(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    """
    Streaming chat endpoint.

    Args:
        request: The validated chat request.
        service: Injected ``ChatService`` instance.

    Returns:
        A ``StreamingResponse`` emitting SSE frames as tokens are generated.
    """
    return StreamingResponse(
        service.stream_chat(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )