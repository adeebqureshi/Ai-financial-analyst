from __future__ import annotations
import platform
import fastapi
from pydantic import BaseModel, ConfigDict, Field
from app.core.constants import APP_NAME, APP_VERSION
class VersionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    app_name: str = Field(default=APP_NAME, description="Application name.")
    app_version: str = Field(default=APP_VERSION, description="Application version.")
    python_version: str = Field(
        default_factory=platform.python_version,
        description="Python interpreter version.",
    )
    fastapi_version: str = Field(
        default_factory=lambda: fastapi.__version__,
        description="Installed FastAPI version.",
    )
    demo_mode: bool = Field(
        default=False,
        description="Whether the application is running in demo mode with synthetic data.",
    )