"""
AI Financial Analyst

Enterprise-grade AI-powered financial analysis platform.

This package contains the core application logic, organized following
Clean Architecture principles:

    - ``app.core``      — Cross-cutting concerns (config, logging, exceptions, constants)
    - ``app.api``       — HTTP/REST interface layer (FastAPI routers)
    - ``app.schemas``   — Pydantic request/response DTOs
    - ``app.services``  — Application use-case orchestration
    - ``app.models``    — Domain entities and ORM models
    - ``app.db``        — Database connection and session management
    - ``app.ingestion`` — Data ingestion pipelines
    - ``app.parsers``   — Financial document parsers (10-K, 10-Q, etc.)
    - ``app.retrievers``— Vector-store retrieval components
    - ``app.agents``    — LLM agent definitions and orchestration
    - ``app.sandbox``   — Code execution sandbox for analytical tasks
    - ``app.evaluation``— Evaluation and benchmarking utilities
    - ``app.utils``     — Shared helper functions

The dependency graph flows inward: outer layers (api, services) depend on
inner layers (core, models), never the reverse.
"""

__version__ = "0.1.0"