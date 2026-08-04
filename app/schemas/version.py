"""
Version Info Schemas

This module defines the Pydantic model for the version endpoint response.
It exposes application metadata (version, name) and runtime information
(Python version, FastAPI version) for debugging and compatibility checks.

Design Decisions:
    - **Runtime metadata included**: Exposing Python and FastAPI versions
      helps with debugging deployment issues and verifying compatibility
      in production environments.
    - **Separate from ``HealthResponse``**: Version info is a distinct
      concern from health status. Keeping them separate follows the
      Single Responsibility Principle.
"""

from __future__ import annotations

import platform

import fastapi
from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import APP_NAME, APP_VERSION


class VersionResponse(BaseModel):
    """
    Application and runtime version information.

    Attributes:
        app_name: Human-readable application name.
        app_version: Application semantic version.
        python_version: Python interpreter version string.
        fastapi_version: Installed FastAPI version string.
    """

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