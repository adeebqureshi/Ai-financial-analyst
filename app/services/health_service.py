from __future__ import annotations
from typing import Any
from app.core.config import Settings
from app.core.constants import APP_VERSION, Environment
from app.core.logging import get_logging_status
from app.schemas.health import ComponentHealth, HealthResponse, HealthStatus
class HealthService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
    def check_health(self) -> HealthResponse:
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
        return ComponentHealth(
            name="application",
            status=HealthStatus.HEALTHY,
            details={
                "app_name": self._settings.app_name,
                "debug": self._settings.debug,
            },
        )
    def _check_configuration(self) -> ComponentHealth:
        details: dict[str, Any] = {
            "environment": self._settings.environment.value,
        }
        has_openai_key = bool(self._settings.openai_api_key_str)
        # FreeLLMAPI (OpenAI-compatible) also satisfies the LLM requirement.
        has_llm_credentials = has_openai_key or self._settings.uses_freellmapi
        details["openai_api_key_set"] = has_openai_key
        details["freellmapi_configured"] = self._settings.uses_freellmapi
        if self._settings.environment in (Environment.PRODUCTION, Environment.STAGING):
            if not has_llm_credentials:
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
        if any(c.status == HealthStatus.UNHEALTHY for c in components):
            return HealthStatus.UNHEALTHY
        if any(c.status == HealthStatus.DEGRADED for c in components):
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY