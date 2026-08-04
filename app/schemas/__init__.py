"""
Schemas Package

This package contains all Pydantic v2 request/response schemas (DTOs) for
the AI Financial Analyst API.

Submodules:
    - ``base``:   Standard ``APIResponse[T]`` wrapper, error details, metadata.
    - ``health``: Health check response schemas.
    - ``version``: Version info response schemas.

Typical imports from routers::

    from app.schemas import APIResponse, HealthResponse, VersionResponse
"""

from __future__ import annotations

from app.schemas.base import (
    APIResponse,
    ErrorDetail,
    PaginationMeta,
    ResponseMetadata,
)
from app.schemas.health import ComponentHealth, HealthResponse, HealthStatus
from app.schemas.version import VersionResponse

__all__ = [
    # Base
    "APIResponse",
    "ErrorDetail",
    "PaginationMeta",
    "ResponseMetadata",
    # Health
    "ComponentHealth",
    "HealthResponse",
    "HealthStatus",
    # Version
    "VersionResponse",
]