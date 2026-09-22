from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field
T = TypeVar("T")
class ErrorDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    field: str | None = Field(default=None, description="Field name that caused the error.")
    message: str = Field(..., description="Human-readable error message.")
    code: str | None = Field(default=None, description="Machine-readable error code.")
class PaginationMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    page: int = Field(..., ge=1, description="Current page number (1-indexed).")
    page_size: int = Field(..., ge=1, description="Number of items per page.")
    total_items: int = Field(..., ge=0, description="Total number of items.")
    total_pages: int = Field(..., ge=0, description="Total number of pages.")
class ResponseMetadata(BaseModel):
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
class APIResponse(BaseModel, Generic[T]):
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
        metadata = ResponseMetadata(**kwargs)
        return cls(
            success=False,
            message=message,
            data=None,
            errors=errors,
            metadata=metadata,
        )