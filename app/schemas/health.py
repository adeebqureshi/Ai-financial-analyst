"""
Health Check Schemas

This module defines the Pydantic models for health check API responses.
The health endpoint returns the status of the application and its
sub-components (configuration, logging, database, etc.).

Design Decisions:
    - **``HealthStatus`` enum**: Uses ``StrEnum`` for type-safe status values
      (``healthy``, ``degraded``, ``unhealthy``) that serialize directly to
      strings in JSON responses.
    - **``ComponentHealth`` per dependency**: Each subsystem is checked
      individually, allowing clients to identify which component is failing.
    - **``HealthResponse`` aggregates components**: The top-level ``status``
      reflects the worst component status, while ``components`` provides
      per-component detail for diagnostics.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthStatus(StrEnum):
    """
    Health status levels for the application and its components.

    Members:
        HEALTHY: The component is fully operational.
        DEGRADED: The component is partially operational (e.g., slow responses).
        UNHEALTHY: The component is not operational.
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """
    Health status of a single application component.

    Attributes:
        name: Component name (e.g., ``"configuration"``, ``"logging"``).
        status: Current health status of the component.
        details: Optional dictionary with additional diagnostic information
            (e.g., ``{"environment": "development"}``).
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="Component name.")
    status: HealthStatus = Field(..., description="Component health status.")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional diagnostic information.",
    )


class HealthResponse(BaseModel):
    """
    Aggregated health response for the application.

    Attributes:
        status: Overall application health status (worst of all components).
        version: Application version string.
        environment: Current deployment environment.
        components: List of individual component health statuses.
    """

    model_config = ConfigDict(populate_by_name=True)

    status: HealthStatus = Field(..., description="Overall application health status.")
    version: str = Field(..., description="Application version.")
    environment: str = Field(..., description="Current deployment environment.")
    components: list[ComponentHealth] = Field(
        default_factory=list,
        description="Individual component health statuses.",
    )