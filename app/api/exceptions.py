"""
Global Exception Handlers

This module registers exception handlers on the FastAPI application to
ensure all errors — domain exceptions, validation errors, HTTP exceptions,
and unexpected errors — return a consistent ``APIResponse`` JSON structure.

Design Decisions:
    - **Centralized error handling**: All exception handlers are registered
      in one place (``register_exception_handlers``), making it easy to
      audit and extend the error-handling strategy.
    - **Consistent response format**: Every error response uses the
      ``APIResponse.error_response()`` factory, ensuring clients always
      receive the same JSON structure (``success``, ``message``, ``data``,
      ``errors``, ``metadata``).
    - **Domain exceptions mapped to 400/500**: ``FinancialAnalystError``
      subclasses are mapped to appropriate HTTP status codes:
      ``ConfigurationError`` → 500, ``ValidationError`` → 422,
      ``RetrievalError`` → 502, ``ParserError`` → 422,
      ``SandboxError`` → 400.
    - **Generic 500 for unexpected errors**: Unhandled exceptions return a
      500 with a generic message (no internal details leaked to clients)
      and log the full traceback server-side.
    - **No business logic**: Handlers only format and return; they do not
      contain domain logic.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    ConfigurationError,
    FinancialAnalystError,
    ParserError,
    RetrievalError,
    SandboxError,
    ValidationError,
)
from app.core.logging import get_logger
from app.schemas.base import APIResponse, ErrorDetail

logger = get_logger("app.api.exceptions")


# ──────────────────────────────────────────────────────────────────────────────
# Exception → HTTP Status Code Mapping
# ──────────────────────────────────────────────────────────────────────────────

_EXCEPTION_STATUS_MAP: dict[type[Exception], int] = {
    ConfigurationError: 500,
    ValidationError: 422,
    RetrievalError: 502,
    ParserError: 422,
    SandboxError: 400,
}
"""Maps domain exception types to their corresponding HTTP status codes."""


def _get_status_code_for_domain_error(exc: FinancialAnalystError) -> int:
    """
    Determine the HTTP status code for a domain exception.

    Checks the exception type against the mapping. Falls back to 500
    for unknown ``FinancialAnalystError`` subclasses.

    Args:
        exc: The domain exception.

    Returns:
        The appropriate HTTP status code.
    """
    for exc_type, status_code in _EXCEPTION_STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return status_code
    return 500


# ──────────────────────────────────────────────────────────────────────────────
# Exception Handlers
# ──────────────────────────────────────────────────────────────────────────────


async def financial_anyst_error_handler(
    request: Request,
    exc: FinancialAnalystError,
) -> JSONResponse:
    """
    Handle ``FinancialAnalystError`` and its subclasses.

    Converts domain exceptions into structured ``APIResponse`` JSON
    responses with the appropriate HTTP status code.

    Args:
        request: The incoming request that caused the exception.
        exc: The domain exception.

    Returns:
        A ``JSONResponse`` with the error details.
    """
    status_code = _get_status_code_for_domain_error(exc)

    logger.warning(
        "Domain exception: %s (code=%s) | %s %s | %d",
        exc.__class__.__name__,
        exc.error_code,
        request.method,
        request.url.path,
        status_code,
    )

    error_detail = ErrorDetail(
        message=exc.message,
        code=exc.error_code,
    )

    response = APIResponse.error_response(
        message=exc.message,
        errors=[error_detail],
    )

    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode="json"),
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle FastAPI ``RequestValidationError`` (Pydantic validation failures).

    Converts Pydantic validation errors into structured ``APIResponse``
    JSON responses with field-level error details.

    Args:
        request: The incoming request that caused the exception.
        exc: The validation exception.

    Returns:
        A ``JSONResponse`` with validation error details (HTTP 422).
    """
    logger.warning(
        "Validation error: %s %s | %s",
        request.method,
        request.url.path,
        exc.errors(),
    )

    errors: list[ErrorDetail] = []
    for error in exc.errors():
        # Extract field name from the error location
        loc: tuple[Any, ...] = error.get("loc", ())
        field: str = ".".join(str(part) for part in loc if part != "body") or None  # type: ignore[assignment]

        errors.append(
            ErrorDetail(
                field=field,
                message=error.get("msg", "Validation error"),
                code=error.get("type"),
            )
        )

    response = APIResponse.error_response(
        message="Request validation failed",
        errors=errors,
    )

    return JSONResponse(
        status_code=422,
        content=response.model_dump(mode="json"),
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    Handle Starlette ``HTTPException`` (e.g., 404 Not Found, 403 Forbidden).

    Converts HTTP exceptions into structured ``APIResponse`` JSON responses.

    Args:
        request: The incoming request that caused the exception.
        exc: The HTTP exception.

    Returns:
        A ``JSONResponse`` with the error details.
    """
    logger.info(
        "HTTP exception: %s %s | %d",
        request.method,
        request.url.path,
        exc.status_code,
    )

    error_detail = ErrorDetail(
        message=str(exc.detail),
        code=f"HTTP_{exc.status_code}",
    )

    response = APIResponse.error_response(
        message=str(exc.detail),
        errors=[error_detail],
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json"),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle all unhandled exceptions (catch-all).

    Returns a generic 500 Internal Server Error without leaking internal
    details to the client. The full traceback is logged server-side.

    Args:
        request: The incoming request that caused the exception.
        exc: The unhandled exception.

    Returns:
        A ``JSONResponse`` with a generic error message (HTTP 500).
    """
    logger.exception(
        "Unhandled exception: %s %s | %s: %s",
        request.method,
        request.url.path,
        exc.__class__.__name__,
        str(exc),
    )

    error_detail = ErrorDetail(
        message="An internal server error occurred. Please try again later.",
        code="INTERNAL_ERROR",
    )

    response = APIResponse.error_response(
        message="An internal server error occurred.",
        errors=[error_detail],
    )

    return JSONResponse(
        status_code=500,
        content=response.model_dump(mode="json"),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Registration Function
# ──────────────────────────────────────────────────────────────────────────────


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all global exception handlers on the FastAPI application.

    This function should be called once during application initialization
    in ``create_app()``.

    Handlers registered (in order of specificity):
        1. ``FinancialAnalystError`` — domain exceptions.
        2. ``RequestValidationError`` — Pydantic validation failures.
        3. ``StarletteHTTPException`` — HTTP exceptions (404, 403, etc.).
        4. ``Exception`` — catch-all for unhandled errors.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(FinancialAnalystError, financial_anyst_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)