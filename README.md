# AI Financial Analyst

Enterprise-grade AI-powered financial analysis platform built with Python 3.12, FastAPI, and Clean Architecture.

## Overview

This project provides the core infrastructure for an AI Financial Analyst system that can ingest SEC filings (10-K, 10-Q, 8-K, etc.), parse financial documents, retrieve relevant data via vector search, and generate analytical insights using LLM agents.

## Architecture

### Clean Architecture

The project follows Clean Architecture principles, where dependencies flow inward — outer layers depend on inner layers, never the reverse:

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                   │
│              app/api/ — Routers, Middleware              │
├─────────────────────────────────────────────────────────┤
│                  Service Layer (Use Cases)                │
│             app/services/ — Orchestration                 │
├─────────────────────────────────────────────────────────┤
│           Domain Layer (Entities + Business Logic)         │
│      app/models/ — app/schemas/ — app/agents/            │
├─────────────────────────────────────────────────────────┤
│              Infrastructure Layer (I/O)                  │
│  app/ingestion/ — app/parsers/ — app/retrievers/         │
│  app/sandbox/ — app/db/ — app/evaluation/                │
├─────────────────────────────────────────────────────────┤
│                 Core Layer (Cross-cutting)                │
│   app/core/ — config, logging, exceptions, constants     │
└─────────────────────────────────────────────────────────┘
```

### SOLID Principles Applied

| Principle | Implementation |
|-----------|---------------|
| **Single Responsibility** | Each module has one job: `config.py` manages settings, `logging.py` manages log output, `exceptions.py` defines errors, `constants.py` holds values. |
| **Open/Closed** | New exception types subclass `FinancialAnalystError` without modifying existing code. New filing types extend `FilingType` enum. |
| **Liskov Substitution** | All exception subclasses are fully substitutable for the base class — they share the same interface (`message`, `error_code`, `details`, `to_dict()`). |
| **Interface Segregation** | `Settings` exposes focused helper properties (`is_production`, `openai_api_key_str`) rather than forcing callers to know internal types. |
| **Dependency Inversion** | `setup_logging()` accepts `Settings` as a parameter — it depends on an abstraction, not a concrete singleton. Outer layers inject settings into inner layers. |

## Project Structure

```
app/
├── __init__.py              # Package marker, version, architecture docs
├── main.py                  # FastAPI application factory + entry point
├── core/                    # Cross-cutting concerns (innermost layer)
│   ├── __init__.py          # Re-exports public API of core modules
│   ├── config.py            # Pydantic Settings configuration + singleton
│   ├── logging.py           # Rich console + rotating file logging
│   ├── exceptions.py        # Domain-specific exception hierarchy
│   └── constants.py         # Centralized constants (no magic numbers)
├── api/                     # FastAPI routers and middleware
├── services/                # Application use-case orchestration
├── models/                  # Domain entities and ORM models
├── schemas/                 # Pydantic request/response DTOs
├── db/                      # Database connection and session management
├── ingestion/               # Data ingestion pipelines (SEC EDGAR, FMP)
├── parsers/                 # Financial document parsers (XBRL, HTML)
├── retrievers/              # Vector store retrieval components
├── agents/                  # LLM agent definitions and orchestration
├── sandbox/                 # Code execution sandbox for analysis
├── evaluation/              # Evaluation and benchmarking utilities
└── utils/                   # Shared helper functions

tests/                       # Comprehensive unit tests
├── conftest.py              # Shared pytest fixtures
├── test_constants.py       # Constants module tests
├── test_exceptions.py       # Exception hierarchy tests
├── test_config.py           # Configuration tests
└── test_logging.py          # Logging tests

configs/                     # YAML/JSON configuration files
docs/                        # Project documentation
storage/                     # Persistent storage (gitignored)
├── raw/                     # Raw downloaded filings
├── parsed/                  # Parsed/structured filing output
├── embeddings/              # Vector embeddings and indices
└── logs/                    # Rotating log files
```

## Core Modules

### `app/core/config.py` — Configuration

Uses `pydantic-settings` to load configuration from environment variables and a `.env` file with full type validation.

**Key features:**
- **Singleton pattern** via `@lru_cache` — thread-safe, lazy initialization
- **Environment-aware** — auto-enables debug mode in development/test
- **Secrets handling** — API keys stored as `SecretStr` to prevent accidental logging
- **Immutability** — `frozen=True` prevents runtime mutation
- **Validation** — field validators for temperature range, chunk overlap, etc.
- **Required key validation** — `validate_required_keys()` checks for API keys at startup

```python
from app.core.config import get_settings

settings = get_settings()
print(settings.app_name)           # "AI Financial Analyst"
print(settings.environment)        # Environment.DEVELOPMENT
print(settings.openai_api_key_str) # "sk-..."
```

### `app/core/logging.py` — Logging

Configures Python's `logging` module with two output channels:

1. **Console** — Colored output via `rich.logging.RichHandler` with tracebacks
2. **File** — Rotating log files via `logging.handlers.RotatingFileHandler`

**Key features:**
- **Idempotent setup** — `setup_logging()` is a no-op after first call (use `force=True` to reconfigure)
- **Auto-configuration** — `get_logger(__name__)` ensures logging is set up before first use
- **Third-party noise reduction** — noisy libraries (httpx, openai, urllib3) capped at WARNING
- **Introspection** — `get_logging_status()` returns a dict for health-check endpoints
- **Graceful shutdown** — `shutdown_logging()` flushes all handlers

```python
from app.core.logging import get_logger

logger = get_logger(__name__)
logger.info("Application started")
logger.error("Failed to parse filing", exc_info=True)
```

**Request/correlation IDs:** every HTTP request gets a correlation ID (minted
or reused from an incoming `X-Request-ID` header). It is returned to clients
in the `X-Request-ID` response header and automatically attached to *every*
log record via a `ContextVar` + logging filter — no parameter threading
needed. Background jobs bind their job ID the same way via
`bind_request_id()`.

> Full details — what is logged, what is intentionally never logged
> (secrets, tokens, prompts, financial payloads), and configuration — are in
> [`docs/OBSERVABILITY.md`](docs/OBSERVABILITY.md).

### `app/core/exceptions.py` — Exception Hierarchy

Defines a domain-specific exception hierarchy rooted at `FinancialAnalystError`:

```
FinancialAnalystError (base)
├── ConfigurationError    — Invalid/missing configuration
├── ValidationError       — Business-rule validation failures
├── RetrievalError        — Data retrieval failures (SEC, FMP, vector store)
├── ParserError           — Document parsing failures (XBRL, HTML)
└── SandboxError          — Code execution failures (timeout, memory limit)
```

**Key features:**
- **Structured metadata** — every exception carries `message`, `error_code`, and `details` dict
- **JSON serialization** — `to_dict()` method for API error responses
- **Distinct default codes** — each subclass has a unique default `error_code`
- **No third-party dependencies** — relies only on the standard library

```python
from app.core.exceptions import ParserError

raise ParserError(
    message="Could not locate 'Income Statement' section in 10-K",
    error_code="PARSE_002",
    details={"filing_type": "10-K", "accession": "0001193125-24-123456"},
)
```

### `app/core/constants.py` — Centralized Constants

Single source of truth for all constant values, eliminating magic numbers:

- **Enums**: `Environment`, `LogLevel`, `FilingType` (type-safe, IDE-autocompletable)
- **`Final` scalars**: timeouts, retry counts, log sizes, URLs, storage paths
- **Immutable collections**: `SUPPORTED_FILING_TYPES` is a `frozenset`
- **Financial document data**: standard statement sections, key financial metrics

```python
from app.core.constants import FilingType, SUPPORTED_FILING_TYPES

print(FilingType.FORM_10K)              # "10-K"
print("10-K" in SUPPORTED_FILING_TYPES) # True
```

## Getting Started

### Prerequisites

- Python 3.12+
- pip

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-financial-analyst

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[dev]"
```

### Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your API keys:
   ```env
   OPENAI_API_KEY=sk-your-key-here
   SEC_API_KEY=your-sec-key
   FMP_API_KEY=your-fmp-key
   ENVIRONMENT=development
   LOG_LEVEL=INFO
   ```

### Running the Application

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload

# Or run directly
python -m app.main
```

The API will be available at `http://localhost:8000`.

- **Health check**: `GET /health`
- **API docs**: `http://localhost:8000/docs` (Swagger UI)

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing
```

## Database Migrations

This project uses **Alembic** for database schema migrations. Two separate migration histories are maintained:

- **Authentication database** (`auth_alembic_version`): `users` table
- **Chat database** (`chat_alembic_version`): `chat_sessions`, `chat_messages` tables

### Running Migrations

```bash
# Apply all auth migrations (PostgreSQL production)
export AUTH_DATABASE_URL="postgresql+psycopg://user:pass@host:5432/db"
alembic -c alembic.ini -x database=auth upgrade head

# Apply all chat migrations (PostgreSQL production)
export CHAT_DATABASE_URL="postgresql+psycopg://user:pass@host:5432/db"
alembic -c alembic.ini -x database=chat upgrade head
```

### Creating New Migrations

```bash
# Generate a new auth migration (auto-detect model changes)
alembic -c alembic.ini -x database=auth revision --autogenerate -m "add column to users"

# Generate a new chat migration (auto-detect model changes)
alembic -c alembic.ini -x database=chat revision --autogenerate -m "add index to chat_messages"
```

### Migration Commands Reference

| Command | Description |
|---------|-------------|
| `upgrade head` | Apply all pending migrations |
| `upgrade +1` | Apply next migration |
| `downgrade -1` | Rollback last migration |
| `downgrade base` | Rollback all migrations |
| `current` | Show current revision |
| `history` | Show migration history |
| `show <rev>` | Show migration details |
| `revision -m "msg"` | Create empty migration |
| `revision --autogenerate -m "msg"` | Create migration from model changes |

### Development vs Production

- **Development/Tests (SQLite)**: Uses `Base.metadata.create_all()` automatically — no migration commands needed
- **Production (PostgreSQL)**: Uses Alembic migrations — run `upgrade head` on deploy or let the application run them on startup

The application automatically runs migrations on startup when PostgreSQL is configured. For zero-downtime deployments, run migrations manually before deploying new code.

## Architectural Decisions

### Why Pydantic Settings over `os.environ`?

Pydantic Settings provides type validation, default values, `.env` file support, and immutability out of the box. Invalid values raise `ValidationError` at startup, failing fast rather than at runtime.

### Why `lru_cache` for the singleton?

`functools.lru_cache` is thread-safe, lazy, and can be reset in tests via `cache_clear()`. It avoids the complexity of custom singleton classes or module-level globals.

### Why Rich for console logging?

`RichHandler` provides colored log levels, timestamps, and rich traceback rendering without third-party logging frameworks. It integrates with any `logging.Logger` and degrades gracefully in non-TTY environments.

### Why `StrEnum` instead of `Enum`?

`StrEnum` (Python 3.11+) makes enum members strings, enabling direct comparison with string values from environment variables, API responses, and configuration files without `.value` access.

### Why a frozen Pydantic model?

`frozen=True` prevents runtime mutation of configuration, eliminating a class of concurrency bugs where one part of the application changes settings that another part depends on.

### Why `SecretStr` for API keys?

`SecretStr` prevents accidental logging or serialization of sensitive values. The key is only exposed via the explicit `get_secret_value()` method or the `*_str` helper properties.

## License

See [LICENSE](LICENSE) for details.# Ai-financial-analyst
