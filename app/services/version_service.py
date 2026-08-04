"""
Version Info Service

This module contains the business logic for retrieving application and
runtime version information.

Design Decisions:
    - **Service class, not functions**: Consistent with ``HealthService``,
      using a class allows dependency injection and testability.
    - **No I/O**: Version info is static metadata; no database or API
      calls are needed. The service simply assembles the data.
    - **Separate from health**: Version info is a distinct concern from
      health status, following the Single Responsibility Principle.
"""

from __future__ import annotations

from app.core.config import Settings
from app.schemas.version import VersionResponse


class VersionService:
    """
    Service for retrieving application version information.

    This service assembles version metadata from the application settings
    and runtime environment.

    Attributes:
        _settings: The application settings instance.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the version service.

        Args:
            settings: The application settings instance.
        """
        self._settings = settings

    def get_version_info(self) -> VersionResponse:
        """
        Retrieve application and runtime version information.

        Returns:
            A ``VersionResponse`` with app name, version, Python version,
            and FastAPI version.
        """
        return VersionResponse(
            app_name=self._settings.app_name,
            app_version=self._settings.app_version,
        )