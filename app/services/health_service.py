"""
Health Check Service

This module contains the business logic for performing application health
checks. The service inspects core components (configuration, logging) and
returns a structured ``HealthResponse``.

Design Decisions:
    - **Service class, not functions**: Encapsulating health-check logic in a
      class allows dependency injection (``Settings`` is passed to the
      constructor) and makes the service mockable in tests.
    - **Component-based checks**: Each subsystem is checked independently,
      allowing the health endpoint to report which specific component is
      failing rather than a binary "up/down".
    - **No I/O in constructor**: The service is lightweight to instantiate;
      health checks are performed lazily in ``check_health()``.
    - **Worst-status aggregation**: The overall status is the worst of all
      component statuses, so a single failing component degrades the entire
      application status.
"""

from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.core.constants import APP_VERSION, Environment
from app.core.logging import get_logging_status
from app.schemas.health import ComponentHealth, HealthResponse, HealthStatus


class HealthService:
    """
    Service for performing application health checks.

    This service checks the status of core application components and
    aggregates them into a single ``HealthResponse``.

    Attributes:
        _settings: The application settings instance used for checks.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the health service.

        Args:
            settings: The application settings instance.
        """
        self._settings = settings

    def check_health(self) -> HealthResponse:
        """
        Perform a health check of all application components.

        Checks the following components:
            - **application**: Always healthy if the service is running.
            - **configuration**: Verifies settings are loaded and valid.
            - **logging**: Verifies logging is configured.

        Returns:
            A ``HealthResponse`` with the overall status and per-component
            details.
        """
        components: list[ComponentHealth] = [
            self._check_application(),
            self._check_configuration(),
            self._check_logging(),
        ]

        overall_status = self._aggregate_status(components)

        return HealthResponse(
            status=overall_status,
            version=APP_VERSION,
            environment=self._settings.environment.value,
            components=components,
        )

    def _check_application(self) -> ComponentHealth:
        """
        Check the application component status.

        The application is considered healthy if this service is running
        and can respond.

        Returns:
            A ``ComponentHealth`` for the application.
        """
        return ComponentHealth(
            name="application",
            status=HealthStatus.HEALTHY,
            details={
                "app_name": self._settings.app_name,
                "debug": self._settings.debug,
            },
        )

    def _check_configuration(self) -> ComponentHealth:
        """
        Check the configuration component status.

        Verifies that settings are loaded and the environment is valid.

        Returns:
            A ``ComponentHealth`` for the configuration.
        """
        details: dict[str, Any] = {
            "environment": self._settings.environment.value,
        }

        # Check if required API keys are set (without raising)
        has_openai_key = bool(self._settings.openai_api_key_str)
        details["openai_api_key_set"] = has_openai_key

        if self._settings.environment in (Environment.PRODUCTION, Environment.STAGING):
            if not has_openai_key:
                return ComponentHealth(
                    name="configuration",
                    status=HealthStatus.DEGRADED,
                    details=details,
                )

        return ComponentHealth(
            name="configuration",
            status=HealthStatus.HEALTHY,
            details=details,
        )

    def _check_logging(self) -> ComponentHealth:
        """
        Check the logging component status.

        Verifies that logging has been configured.

        Returns:
            A ``ComponentHealth`` for the logging subsystem.
        """
        log_status = get_logging_status()
        is_configured: bool = log_status.get("configured", False)

        status = HealthStatus.HEALTHY if is_configured else HealthStatus.DEGRADED

        return ComponentHealth(
            name="logging",
            status=status,
            details={
                "configured": is_configured,
                "level": log_status.get("level", "UNKNOWN"),
                "handlers": log_status.get("handlers", []),
            },
        )

    @staticmethod
    def _aggregate_status(components: list[ComponentHealth]) -> HealthStatus:
        """
        Determine the overall status from component statuses.

        The overall status is the worst (most severe) of all component
        statuses. Priority: ``UNHEALTHY > DEGRADED > HEALTHY``.

        Args:
            components: List of component health statuses.

        Returns:
            The aggregated overall health status.
        """
        if any(c.status == HealthStatus.UNHEALTHY for c in components):
            return HealthStatus.UNHEALTHY
        if any(c.status == HealthStatus.DEGRADED for c in components):
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY