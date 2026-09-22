from __future__ import annotations
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
class ComponentHealth(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str = Field(..., description="Component name.")
    status: HealthStatus = Field(..., description="Component health status.")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional diagnostic information.",
    )
class HealthResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    status: HealthStatus = Field(..., description="Overall application health status.")
    version: str = Field(..., description="Application version.")
    environment: str = Field(..., description="Current deployment environment.")
    components: list[ComponentHealth] = Field(
        default_factory=list,
        description="Individual component health statuses.",
    )