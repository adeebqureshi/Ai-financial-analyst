"""
Health Router

This module defines the health check endpoint (``GET /health``) which
returns the status of the application and its sub-components.

Design Decisions:
    - **No business logic in route**: The route handler delegates entirely
      to ``HealthService.check_health()``. The route only parses input,
      calls the service, and wraps the result in ``APIResponse``.
    - **Dependency injection**: ``HealthService`` is injected via
      ``Depends(get_health_service)``, making it overridable in tests.
    - **Standard response format**: Returns ``APIResponse[HealthResponse]``
      for consistency with all other endpoints.
    - **No auth required**: Health checks must be accessible without
      authentication for load balancers and monitoring tools.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_health_service
from app.schemas.base import APIResponse
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=APIResponse[HealthResponse],
    summary="Health check",
    description="Returns the health status of the application and its components.",
)
async def health_check(
    service: HealthService = Depends(get_health_service),
) -> APIResponse[HealthResponse]:
    """
    Health check endpoint.

    Checks the status of core application components (application,
    configuration, logging) and returns an aggregated health response.

    Args:
        service: Injected ``HealthService`` instance.

    Returns:
        An ``APIResponse`` containing the health status, version,
        environment, and per-component details.
    """
    health_data = service.check_health()

    return APIResponse.success_response(
        message="Health check completed",
        data=health_data,
    )