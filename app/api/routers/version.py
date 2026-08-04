"""
Version Router

This module defines the version info endpoint (``GET /version``) which
returns application and runtime version information.

Design Decisions:
    - **No business logic in route**: The route handler delegates entirely
      to ``VersionService.get_version_info()``.
    - **Dependency injection**: ``VersionService`` is injected via
      ``Depends(get_version_service)``.
    - **Standard response format**: Returns ``APIResponse[VersionResponse]``
      for consistency with all other endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_version_service
from app.schemas.base import APIResponse
from app.schemas.version import VersionResponse
from app.services.version_service import VersionService

router = APIRouter(prefix="/version", tags=["Version"])


@router.get(
    "",
    response_model=APIResponse[VersionResponse],
    summary="Version information",
    description="Returns application name, version, and runtime metadata.",
)
async def version_info(
    service: VersionService = Depends(get_version_service),
) -> APIResponse[VersionResponse]:
    """
    Version info endpoint.

    Returns application name, version, Python version, and FastAPI version.

    Args:
        service: Injected ``VersionService`` instance.

    Returns:
        An ``APIResponse`` containing version and runtime information.
    """
    version_data = service.get_version_info()

    return APIResponse.success_response(
        message="Version information retrieved",
        data=version_data,
    )