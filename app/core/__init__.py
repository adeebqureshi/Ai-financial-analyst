"""
Core Package

This package contains cross-cutting infrastructure shared across all layers
of the AI Financial Analyst application. It is the innermost ring in the
Clean Architecture dependency graph and must not depend on outer layers
(api, services, etc.).

Submodules:
    - ``config``:      Pydantic Settings configuration and singleton accessor.
    - ``logging``:     Rich console + rotating file logging setup.
    - ``exceptions``:  Domain-specific exception hierarchy.
    - ``constants``:  Centralized, immutable constant values.

Typical imports from outer layers::

    from app.core.config import get_settings
    from app.core.logging import get_logger
    from app.core.exceptions import FinancialAnalystError, ParserError
    from app.core.constants import FilingType, Environment
"""

from __future__ import annotations

from app.core.config import Settings, get_project_root, get_settings
from app.core.constants import (
    APP_NAME,
    APP_VERSION,
    Environment,
    FilingType,
    LogLevel,
    SUPPORTED_FILING_TYPES,
)
from app.core.exceptions import (
    ConfigurationError,
    FinancialAnalystError,
    ParserError,
    RetrievalError,
    SandboxError,
    ValidationError,
)
from app.core.logging import get_logger, get_logging_status, setup_logging, shutdown_logging

__all__ = [
    # Config
    "Settings",
    "get_settings",
    "get_project_root",
    # Constants
    "APP_NAME",
    "APP_VERSION",
    "Environment",
    "FilingType",
    "LogLevel",
    "SUPPORTED_FILING_TYPES",
    # Exceptions
    "FinancialAnalystError",
    "ConfigurationError",
    "ValidationError",
    "RetrievalError",
    "ParserError",
    "SandboxError",
    # Logging
    "get_logger",
    "setup_logging",
    "shutdown_logging",
    "get_logging_status",
]