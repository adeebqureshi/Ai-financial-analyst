"""
AI Financial Analyst — Application Entry Point

This module provides the FastAPI application factory and ASGI entry point.
It wires together all layers of the Clean Architecture:

    - **Core layer**: Configuration, logging, exceptions, constants.
    - **API layer**: Routers, middleware, dependency injection, exception handlers.
    - **Service layer**: Health and version services.

Design Decisions:
    - **Application factory pattern** (``create_app``): Allows test isolation
      (create an app with overridden settings) and deferred initialization
      (the app is only created when imported, not at module load time).
    - **CORS configuration**: Environment-aware — permissive in development
      (all origins), restrictive in production (configurable origins).
    - **Middleware registration**: ``RequestLoggingMiddleware`` is added
      via ``app.middleware("http")`` for automatic request/response logging.
    - **Swagger customization**: Professional API documentation with
      title, description, version, contact, license, tags, and servers.
    - **Startup/shutdown events**: Clean lifecycle management — logging
      is set up on startup and flushed on shutdown.
    - **Module-level ``app``**: The ``app = create_app()`` line allows ASGI
      servers (Uvicorn, Gunicorn) to import the application directly.

Usage:
    Development::

        uvicorn app.main:app --reload

    Production::

        gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import Contact, License

from app.api import RequestLoggingMiddleware, api_router, register_exception_handlers
from app.core.config import Settings, get_settings
from app.core.constants import APP_NAME, APP_VERSION
from app.core.logging import get_logger, setup_logging, shutdown_logging

# Initialize logging at import time so all modules get a configured logger.
setup_logging()
logger = get_logger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Swagger / OpenAPI Metadata
# ──────────────────────────────────────────────────────────────────────────────

_TAGS_METADATA: list[dict[str, str]] = [
    {
        "name": "Root",
        "description": "Root endpoint with application information and API discovery.",
    },
    {
        "name": "Health",
        "description": "Application health check endpoint for monitoring and load balancers.",
    },
    {
        "name": "Version",
        "description": "Application and runtime version information.",
    },
]
"""OpenAPI tag metadata for organized Swagger UI documentation."""

_CONTACT: Contact = Contact(
    name="AI Financial Analyst Team",
    url="https://github.com/adeeb/ai-financial-analyst",
)
"""Contact information displayed in the Swagger UI."""

_LICENSE: License = License(
    name="MIT",
    url="https://opensource.org/licenses/MIT",
)
"""License information displayed in the Swagger UI."""


# ──────────────────────────────────────────────────────────────────────────────
# CORS Configuration
# ──────────────────────────────────────────────────────────────────────────────


def _get_cors_origins(settings: Settings) -> list[str]:
    """
    Return allowed CORS origins based on the environment.

    In development, all origins are allowed (``["*"]``).
    In production/staging, only configured origins are allowed.

    Args:
        settings: The application settings.

    Returns:
        A list of allowed origin strings.
    """
    if settings.is_development or settings.is_test:
        return ["*"]
    # In production, restrict to known origins.
    # This can be extended to read from settings in the future.
    return [
        "https://localhost:3000",
        "https://ai-financial-analyst.example.com",
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Application Factory
# ──────────────────────────────────────────────────────────────────────────────


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Create and configure a FastAPI application instance.

    This factory function:
        1. Resolves settings (uses singleton if not provided).
        2. Configures logging.
        3. Creates the FastAPI app with Swagger customization.
        4. Registers CORS middleware.
        5. Registers request logging middleware.
        6. Registers all API routers.
        7. Registers global exception handlers.
        8. Registers startup/shutdown event handlers.

    Args:
        settings: Optional ``Settings`` instance. If ``None``, the singleton
            from ``get_settings()`` is used. Pass a custom instance in tests
            to override configuration.

    Returns:
        A fully configured ``FastAPI`` application instance.
    """
    if settings is None:
        settings = get_settings()

    # Reconfigure logging with the resolved settings
    setup_logging(settings, force=True)
    app_logger = get_logger("app")

    # ── Lifespan (startup/shutdown) ─────────────────────────────────────
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        """
        Manage application startup and shutdown lifecycle.

        On startup, logs the application name, version, environment, and
        debug flag. On shutdown, logs the shutdown and flushes log handlers.

        Args:
            _app: The FastAPI application instance (unused).
        """
        app_logger.info(
            "Starting %s v%s (environment=%s, debug=%s)",
            APP_NAME,
            APP_VERSION,
            settings.environment.value,
            settings.debug,
        )
        yield
        app_logger.info("Shutting down %s", APP_NAME)
        shutdown_logging()

    # ── Create FastAPI app with Swagger customization ───────────────────
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        description=(
            "Enterprise-grade AI-powered financial analysis platform.\n\n"
            "## Features\n"
            "- SEC filing ingestion (10-K, 10-Q, 8-K, etc.)\n"
            "- Financial document parsing (XBRL, HTML)\n"
            "- Vector search retrieval\n"
            "- LLM-powered analytical agents\n"
            "- Code execution sandbox\n\n"
            "## Architecture\n"
            "Built with Clean Architecture and SOLID principles."
        ),
        contact=_CONTACT,
        license_info=_LICENSE,
        openapi_tags=_TAGS_METADATA,
        servers=[
            {"url": "/", "description": "Current server"},
        ],
        lifespan=lifespan,
    )

    # ── CORS Middleware ─────────────────────────────────────────────────
    cors_origins = _get_cors_origins(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request Logging Middleware ─────────────────────────────────────
    app.add_middleware(RequestLoggingMiddleware)

    # ── Register Routers ───────────────────────────────────────────────
    app.include_router(api_router)

    # ── Register Exception Handlers ────────────────────────────────────
    register_exception_handlers(app)

    return app


# ──────────────────────────────────────────────────────────────────────────────
# Module-level ASGI app for direct import by ASGI servers
# ──────────────────────────────────────────────────────────────────────────────

app = create_app()


# ──────────────────────────────────────────────────────────────────────────────
# Development entry point
# ──────────────────────────────────────────────────────────────────────────────


def main() -> None:
    """
    Run the application using Uvicorn (development mode).

    For production, use an ASGI server (Uvicorn/Gunicorn) directly::

        uvicorn app.main:app --host 0.0.0.0 --port 8000
    """
    import uvicorn

    settings = get_settings()
    logger.info("Launching Uvicorn development server")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
    )


if __name__ == "__main__":
    main()