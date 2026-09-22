from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from app.core.config import Settings
from app.core.constants import APP_NAME, APP_VERSION
from app.api.dependencies.settings import get_settings_dep
from app.schemas.base import APIResponse
router = APIRouter(tags=["Root"])
class RootData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str = Field(..., description="Application name.")
    version: str = Field(..., description="Application version.")
    description: str = Field(..., description="Application description.")
    documentation_url: str = Field(..., description="Swagger UI URL.")
    endpoints: dict[str, str] = Field(..., description="Available API endpoints.")
@router.get(
    "/",
    response_model=APIResponse[RootData],
    summary="Root endpoint",
    description="Returns basic application information and available endpoints.",
)
async def root(
    settings: Settings = Depends(get_settings_dep),
) -> APIResponse[RootData]:
    data = RootData(
        name=settings.app_name,
        version=settings.app_version,
        description="Enterprise-grade AI-powered financial analysis platform.",
        documentation_url="/docs",
        endpoints={
            "health": "/health",
            "version": "/version",
            "docs": "/docs",
            "redoc": "/redoc",
        },
    )
    return APIResponse.success_response(
        message=f"Welcome to {APP_NAME} v{APP_VERSION}",
        data=data,
    )