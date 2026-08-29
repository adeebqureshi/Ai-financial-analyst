"""
AI Financial Analyst — Application Entry Point

This module provides the FastAPI application factory and ASGI entry point.
It wires together all layers of the Clean Architecture:

- Core layer: Configuration, logging, exceptions, constants.
- API layer: Routers, middleware, dependency injection, exception handlers.
- Service layer: Health and version services.

Design Decisions:
- Application factory pattern (create_app): Allows test isolation and deferred initialization.
- CORS configuration: Environment-aware — permissive in development, restrictive in production.
- Middleware registration: RequestLoggingMiddleware is added for automatic request/response logging.
- Swagger customization: Professional API documentation with title, description, version, contact, license, tags, and servers.
- Startup/shutdown events: Clean lifecycle management — logging is set up on startup and flushed on shutdown.
- Module-level app: The app = create_app() line allows ASGI servers to import the application directly.

Usage:
Development:
    uvicorn app.main:app --reload

Production:
    gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import Contact, License

from app.api import RequestLoggingMiddleware, api_router, register_exception_handlers
from app.core.config import Settings, get_settings
from app.core.constants import APP_NAME, APP_VERSION
from app.core.logging import get_logger, setup_logging, shutdown_logging

setup_logging()
logger = get_logger(__name__)

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
    {
        "name": "Analysis",
        "description": "Comprehensive AI-driven financial analysis of a company.",
    },
    {
        "name": "Search",
        "description": "Semantic search over the retrieval engine.",
    },
    {
        "name": "Company",
        "description": "Company profile information by ticker symbol.",
    },
    {
        "name": "Valuation",
        "description": "Discounted cash flow (DCF) valuation and intrinsic value calculations.",
    },
    {
        "name": "Chat",
        "description": "Conversational AI financial analyst chat.",
    },
    {
        "name": "Financial Ratios",
        "description": "Financial ratio calculations from financial statements.",
    },
    {
        "name": "Risk",
        "description": "Financial risk analysis using Piotroski, Altman, and Beneish scores.",
    },
    {
        "name": "Report",
        "description": "LLM-powered financial report generation.",
    },
    {
        "name": "Compare",
        "description": "Multi-company comparison using common valuation parameters.",
    },
    {
        "name": "Screen",
        "description": "Stock screening based on financial health and valuation criteria.",
    },
    {
        "name": "Documents",
        "description": "Financial PDF upload, indexing, retrieval and document library.",
    },
]

_CONTACT = Contact(
    name="AI Financial Analyst Team",
    url="https://github.com/adeeb/ai-financial-analyst",
)

_LICENSE = License(
    name="MIT",
    url="https://opensource.org/licenses/MIT",
)


def _get_cors_origins(settings: Settings) -> list[str]:
    """
    Return allowed CORS origins based on the environment.
    """
    if settings.is_development or settings.is_test:
        return ["*"]

    return [
        "https://localhost:3000",
        "https://ai-financial-analyst.example.com",
    ]


def _run_startup_infrastructure_checks(settings: Settings, logger: Any) -> None:
    """
    Verify infrastructure reachability on startup (best-effort, never raises).

    PostgreSQL and Redis are optional at boot: the application degrades to
    SQLite / local-memory fallbacks, but the operator gets an explicit log
    signal when the production services are not reachable. Skipped in the
    test environment so unit tests never probe (or wait on) real services.
    """
    if settings.is_test:
        return

    try:
        from app.infrastructure.container import Container

        container = Container()
        checks = container.health()
        container.close()

        for component, ok in checks.items():
            if ok:
                logger.info("Infrastructure check passed: %s", component)
            else:
                logger.warning(
                    "Infrastructure check FAILED: %s (falling back to local resources)",
                    component,
                )
    except Exception as exc:  # pragma: no cover - defensive best-effort
        logger.warning("Infrastructure startup checks skipped: %s", exc)


def _run_shutdown_disposal(settings: Settings, logger: Any) -> None:
    """
    Dispose pooled database connections on shutdown (best-effort).

    Ensures gunicorn/uvicorn worker recycling never leaks PostgreSQL or Redis
    connections. Each disposal step is independent and failures are swallowed.
    """
    try:
        from app.auth import database as auth_database
        from app.chat import database as chat_database

        chat_database.dispose_all_engines()
        auth_database.dispose_all_engines()
        logger.info("Database connection pools disposed")
    except Exception as exc:  # pragma: no cover - defensive best-effort
        logger.warning("Shutdown disposal skipped: %s", exc)

    try:
        from app.api.rate_limiter import reset_rate_limiter

        reset_rate_limiter()
    except Exception:  # pragma: no cover - defensive best-effort
        pass


def _run_chat_retention_cleanup(settings: Settings, logger: Any) -> None:
    """
    Best-effort purge of expired chat sessions on startup.

    Retention cleanup is non-critical: any failure (unreachable database,
    missing schema, ...) is logged and swallowed so the application still boots.
    """
    try:
        from app.chat.store import ChatStore

        store = ChatStore(
            settings.chat_database_url,
            retention_days=settings.chat_retention_days,
        )
        removed = store.purge_expired()
        if removed:
            logger.info("Chat retention cleanup removed %s expired session(s)", removed)
    except Exception as exc:  # pragma: no cover - defensive best-effort
        logger.warning("Chat retention cleanup skipped: %s", exc)


def _run_database_migrations(settings: Settings, logger: Any) -> None:
    """
    Run database migrations on startup for PostgreSQL databases.

    This ensures the schema is up to date before the application starts
    accepting requests. On SQLite (development/tests), this is a no-op
    since init_db() uses create_all for zero-config setup.

    Any failure is logged and re-raised to prevent the application from
    starting with an outdated schema in production.
    """
    if settings.is_test:
        return

    # Run auth migrations
    if settings.auth_database_url.startswith("postgresql"):
        try:
            from app.auth.database import init_db

            init_db(settings)
            logger.info("Authentication database migrations applied")
        except Exception as exc:
            logger.error("Failed to apply authentication database migrations: %s", exc)
            raise

    # Run chat migrations
    if settings.chat_database_url.startswith("postgresql"):
        try:
            from app.chat.database import init_db as init_chat_db

            init_chat_db(settings.chat_database_url)
            logger.info("Chat database migrations applied")
        except Exception as exc:
            logger.error("Failed to apply chat database migrations: %s", exc)
            raise


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Create and configure a FastAPI application instance.
    """
    if settings is None:
        settings = get_settings()

    setup_logging(settings, force=True)
    app_logger = get_logger("app")

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        app_logger.info(
            "Starting %s v%s (environment=%s, debug=%s)",
            APP_NAME,
            APP_VERSION,
            settings.environment.value,
            settings.debug,
        )

        _run_startup_infrastructure_checks(settings, app_logger)
        _run_database_migrations(settings, app_logger)
        _run_chat_retention_cleanup(settings, app_logger)

        yield

        app_logger.info("Shutting down %s", APP_NAME)
        _run_shutdown_disposal(settings, app_logger)
        shutdown_logging()

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
        servers=[{"url": "/", "description": "Current server"}],
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_get_cors_origins(settings),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(api_router)
    register_exception_handlers(app)

    return app


app = create_app()


def main() -> None:
    """
    Run the application using Uvicorn (development mode).
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