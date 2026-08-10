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
        yield
        app_logger.info("Shutting down %s", APP_NAME)
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