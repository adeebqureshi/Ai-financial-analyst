"""
API Dependencies Package

This package contains FastAPI dependency injection callables for settings
and services. Dependencies are injected into route handlers via
``Depends()``, making them explicit, testable, and overridable.

Submodules:
    - ``settings``: Settings singleton dependency.
    - ``services``: Service factory dependencies (health, version).
"""

from __future__ import annotations

from app.api.dependencies.services import (
    get_analysis_service,
    get_chat_service,
    get_company_service,
    get_compare_service,
    get_health_service,
    get_ratios_service,
    get_report_service,
    get_risk_service,
    get_screen_service,
    get_search_service,
    get_valuation_service,
    get_version_service,
)
from app.api.dependencies.settings import get_settings_dep

__all__ = [
    "get_settings_dep",
    "get_health_service",
    "get_version_service",
    "get_analysis_service",
    "get_search_service",
    "get_company_service",
    "get_valuation_service",
    "get_chat_service",
    "get_ratios_service",
    "get_risk_service",
    "get_report_service",
    "get_compare_service",
    "get_screen_service",
]
