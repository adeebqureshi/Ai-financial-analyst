"""
Base Pydantic Schemas — Standard API Response Models

This module defines the foundational schemas used across all API endpoints
to ensure a consistent, predictable response contract.

Design Decisions:
    - **Generic ``APIResponse[T]``**: A single generic wrapper model allows
      every endpoint to return the same JSON structure (``success``,
      ``message``, ``data``, ``errors``, ``metadata``) while preserving
      type safety for the ``data`` payload via Pydantic's generic support.
    - **``ErrorDetail`` over raw strings**: Structured error objects carry
      ``field``, ``message``, and ``code``, enabling clients to map
      validation errors back to form fields programmatically.
    - **``ResponseMetadata`` with timestamp**: Every response includes a
      timestamp and optional ``request_id`` for tracing and debugging.
    - **``PaginationMeta``**: Reusable pagination metadata that can be
      attached to any list response, avoiding per-endpoint duplication.
    - **Pydantic v2 ``model_config``**: All models use
      ``ConfigDict(populate_by_name=True)`` to support both snake_case
      (Python) and camelCase (JSON) field names if needed in the future.

Usage:
    >>> from app.schemas.base import APIResponse
    >>> from app.schemas.health import HealthResponse
    >>>
    >>> response = APIResponse[HealthResponse](
    ...     success=True,
    ...     message="Health check completed",
    ...     data=HealthResponse(status="healthy", version="0.1.0"),
    ... )
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# ──────────────────────────────────────────────────────────────────────────────
# Type Variable for Generic APIResponse
# ──────────────────────────────────────────────────────────────────────────────

T = TypeVar("T")
"""Type variable representing the data payload type in ``APIResponse``."""


# ──────────────────────────────────────────────────────────────────────────────
# Error Schemas
# ──────────────────────────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    """
    Structured error detail for API error responses.

    Attributes:
        field: The field name that caused the error (``None`` for non-field
            errors). Useful for mapping validation errors to form fields.
        message: Human-readable error message.
        code: Machine-readable error code (e.g., ``"REQUIRED"``,
            ``"INVALID_FORMAT"``).
    """

    model_config = ConfigDict(populate_by_name=True)

    field: str | None = Field(default=None, description="Field name that caused the error.")
    message: str = Field(..., description="Human-readable error message.")
    code: str | None = Field(default=None, description="Machine-readable error code.")


# ──────────────────────────────────────────────────────────────────────────────
# Metadata Schemas
# ──────────────────────────────────────────────────────────────────────────────


class PaginationMeta(BaseModel):
    """
    Pagination metadata for list responses.

    Attributes:
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        total_items: Total number of items across all pages.
        total_pages: Total number of pages.
    """

    model_config = ConfigDict(populate_by_name=True)

    page: int = Field(..., ge=1, description="Current page number (1-indexed).")
    page_size: int = Field(..., ge=1, description="Number of items per page.")
    total_items: int = Field(..., ge=0, description="Total number of items.")
    total_pages: int = Field(..., ge=0, description="Total number of pages.")


class ResponseMetadata(BaseModel):
    """
    Metadata attached to every API response.

    Attributes:
        timestamp: UTC timestamp when the response was generated.
        request_id: Optional correlation ID for request tracing.
        pagination: Optional pagination metadata for list responses.
    """

    model_config = ConfigDict(populate_by_name=True)

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the response.",
    )
    request_id: str | None = Field(
        default=None,
        description="Correlation ID for request tracing.",
    )
    pagination: PaginationMeta | None = Field(
        default=None,
        description="Pagination metadata for list responses.",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Standard API Response
# ──────────────────────────────────────────────────────────────────────────────


class APIResponse(BaseModel, Generic[T]):
    """
    Standard API response wrapper for all endpoints.

    Every API endpoint returns this model as its response, ensuring a
    consistent JSON structure across the entire API surface.

    Attributes:
        success: Whether the request was successful.
        message: Human-readable summary of the result.
        data: The response payload (type ``T``). ``None`` on error.
        errors: List of structured error details. ``None`` on success.
        metadata: Response metadata (timestamp, request ID, pagination).

    Example:
        Success::

            {
                "success": true,
                "message": "Health check completed",
                "data": {"status": "healthy", "version": "0.1.0"},
                "errors": null,
                "metadata": {"timestamp": "2026-01-01T00:00:00Z"}
            }

        Error::

            {
                "success": false,
                "message": "Validation failed",
                "data": null,
                "errors": [
                    {"field": "ticker", "message": "Must be 1-5 letters", "code": "INVALID"}
                ],
                "metadata": {"timestamp": "2026-01-01T00:00:00Z"}
            }
    """

    model_config = ConfigDict(populate_by_name=True)

    success: bool = Field(..., description="Whether the request was successful.")
    message: str = Field(..., description="Human-readable summary of the result.")
    data: T | None = Field(default=None, description="The response payload.")
    errors: list[ErrorDetail] | None = Field(
        default=None,
        description="List of structured error details.",
    )
    metadata: ResponseMetadata = Field(
        default_factory=ResponseMetadata,
        description="Response metadata.",
    )

    @classmethod
    def success_response(
        cls,
        message: str,
        data: T | None = None,
        **kwargs: Any,
    ) -> APIResponse[T]:
        """
        Create a success response.

        Args:
            message: Human-readable success message.
            data: The response payload.
            **kwargs: Additional metadata fields (e.g., ``request_id``).

        Returns:
            An ``APIResponse`` with ``success=True``.
        """
        metadata = ResponseMetadata(**kwargs)
        return cls(
            success=True,
            message=message,
            data=data,
            errors=None,
            metadata=metadata,
        )

    @classmethod
    def error_response(
        cls,
        message: str,
        errors: list[ErrorDetail] | None = None,
        **kwargs: Any,
    ) -> APIResponse[T]:
        """
        Create an error response.

        Args:
            message: Human-readable error summary.
            errors: List of structured error details.
            **kwargs: Additional metadata fields (e.g., ``request_id``).

        Returns:
            An ``APIResponse`` with ``success=False``.
        """
        metadata = ResponseMetadata(**kwargs)
        return cls(
            success=False,
            message=message,
            data=None,
            errors=errors,
            metadata=metadata,
        )