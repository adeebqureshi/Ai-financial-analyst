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
│  app/models/ — app/schemas/ — app/agents/ — app/financial/│
├─────────────────────────────────────────────────────────┤
│              Infrastructure Layer (I/O)                  │
│  app/ingestion/ — app/parsers/ — app/retrieval/          │
│  app/sandbox/ — app/infrastructure/ — app/db/            │
│  app/llm/ — app/vectorstore/ — app/embeddings/           │
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
├── application.py           # Application setup (lifespan, middleware, routes)
├── core/                    # Cross-cutting concerns (innermost layer)
│   ├── __init__.py          # Re-exports public API of core modules
│   ├── config.py            # Pydantic Settings configuration + singleton
│   ├── logging.py           # Rich console + rotating file logging
│   ├── exceptions.py        # Domain-specific exception hierarchy
│   └── constants.py         # Centralized constants (no magic numbers)
├── api/                     # FastAPI routers and middleware
│   ├── dependencies/        # FastAPI dependency injection
│   ├── middleware/          # Custom middleware (CORS, rate limiting, etc.)
│   ├── routes/              # Route modules
│   └── routers/             # APIRouter instances
├── services/                # Application use-case orchestration
├── models/                  # Domain entities and ORM models
├── schemas/                 # Pydantic request/response DTOs
├── db/                      # Database connection and session management
├── ingestion/               # Data ingestion pipelines (SEC EDGAR, FMP)
├── parsers/                 # Financial document parsers (XBRL, HTML)
├── retrieval/               # Vector store retrieval components
├── agents/                  # LLM agent definitions and orchestration
├── sandbox/                 # Code execution sandbox for analysis
├── evaluation/              # Evaluation and benchmarking utilities
├── financial/               # Financial calculation engines (Piotroski, Altman, etc.)
├── rag/                     # RAG pipeline (embeddings, reranking, hybrid search)
├── auth/                    # Authentication & authorization
├── chat/                    # Chat persistence & session management
├── comparison/              # Company comparison & ranking
├── portfolio/               # Portfolio analytics (Sharpe, CAGR, drawdown)
├── recommendation/          # Investment recommendation engine
├── reports/                 # Report generation (Markdown, structured)
├── embeddings/              # Embedding models & providers
├── enums/                   # Shared enumerations
├── infrastructure/          # Infrastructure adapters (Redis, Postgres, health)
├── llm/                     # LLM providers, clients, streaming
├── orchestrator/            # Workflow orchestration (LangGraph)
├── utils/                   # Shared helper functions
├── vectorstore/             # Vector store implementations (Qdrant, Chroma)
└── workflow/                # Workflow engine (nodes, edges, state)

tests/                       # Comprehensive unit tests (organized by module)
├── conftest.py              # Shared pytest fixtures
├── agents/                  # Agent tests
├── api/                     # API endpoint tests
├── auth/                    # Authentication tests
├── chat/                    # Chat persistence tests
├── clients/                 # External client tests
├── comparison/              # Comparison tests
├── core/                    # Core module tests (config, logging)
├── data/                    # Data model tests
├── embeddings/              # Embedding tests
├── financial/               # Financial engine tests
├── infrastructure/          # Infrastructure tests
├── ingestion/               # Ingestion pipeline tests
├── llm/                     # LLM provider tests
├── models/                  # ORM model tests
├── orchestrator/            # Orchestrator tests
├── parsers/                 # Parser tests
├── portfolio/               # Portfolio analytics tests
├── rag/                     # RAG pipeline tests
├── recommendation/          # Recommendation engine tests
├── reports/                 # Report generation tests
├── retrieval/               # Retrieval tests
├── sandbox/                 # Sandbox tests
├── security/                # Security tests
├── services/                # Service tests
├── storage/                 # Storage tests
├── vectorstore/             # Vector store tests
└── workflow/                # Workflow engine tests

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

### Demo Mode (No API Keys Required)

**For quick evaluation without external credentials**, enable **Demo Mode**:

```bash
# Enable demo mode
echo "DEMO_MODE=true" > .env

# Start the application
uvicorn app.main:app --reload
```

Demo mode provides deterministic synthetic data for **5 companies** (AAPL, MSFT, GOOGL, AMZN, TSLA) with:
- Company profiles and market quotes
- Financial statements (income, balance sheet, cash flow)
- Key ratios, valuation inputs, and risk scores (Piotroski, Altman, Beneish)
- SEC filing metadata and synthetic filing text for RAG/search
- In-memory vector store (no Qdrant required)

All demo values are clearly labeled **[DEMO / SYNTHETIC DATA]** in the UI.
No external API keys, SEC access, or Qdrant instance needed.

**Examiner Quick Start:**
```bash
# 1. Enable demo mode
echo "DEMO_MODE=true" > .env

# 2. Start backend
uvicorn app.main:app --reload

# 3. Start frontend (in separate terminal)
cd frontend && npm run dev

# 4. Open http://localhost:3000
# 5. Navigate to Analysis → Select AAPL (or MSFT, GOOGL, AMZN, TSLA)
# 6. View financial analysis, valuation, risk, recommendation
# 7. Use Search/Chat to query demo filing content
```

### Configuration (Production Mode)

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

### Running the Application (Production Mode)

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload

# Or run directly
python -m app.main
```

The API will be available at `http://localhost:8000`.

- **Health check**: `GET /health`
- **API docs**: `http://localhost:8000/docs` (Swagger UI)
- **Version info**: `GET /version` (shows `demo_mode` status)

### Docker Production Deployment

For production deployments, use Docker Compose with the provided configuration:

1. **Prepare environment configuration**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your production values (required for production):
   # - CORS_ORIGINS: Comma-separated list of allowed frontend origins (e.g., https://app.example.com)
   # - OPENAI_API_KEY: Your OpenAI API key
   # - FMP_API_KEY: Your Financial Modeling Prep API key
   # - AUTH_SECRET_KEY: Generate with: python -c "import secrets; print(secrets.token_hex(32))"
   # - ENVIRONMENT=production (already set in docker-compose.yml)
   ```

2. **Start the production stack**:
   ```bash
   # From the project root
   docker compose -f docker/docker-compose.yml up -d
   ```

3. **Verify deployment**:
   ```bash
   # Check service health
   docker compose -f docker/docker-compose.yml ps
   
   # View logs
   docker compose -f docker/docker-compose.yml logs -f app
   
   # Health check endpoint
   curl http://localhost:8000/health
   ```

**Required environment variables for production** (set in `.env`):
| Variable | Description | Required |
|----------|-------------|----------|
| `CORS_ORIGINS` | Comma-separated allowed frontend origins (e.g., `https://app.example.com,https://www.example.com`) | Yes |
| `OPENAI_API_KEY` | OpenAI API key for LLM and embeddings | Yes |
| `FMP_API_KEY` | Financial Modeling Prep API key for market data fallback | Yes |
| `AUTH_SECRET_KEY` | JWT signing secret (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) | Yes |
| `ENVIRONMENT` | Set to `production` (configured in docker-compose.yml) | Yes |

**Optional but recommended for production**:
| Variable | Description |
|----------|-------------|
| `SEC_API_KEY` | SEC EDGAR API key for filing enrichment |
| `LLAMA_PARSE_API_KEY` | LlamaParse API key for advanced PDF parsing |
| `LOG_LEVEL` | Set to `INFO` or `WARNING` for production |

**Demo Mode with Docker** (no API keys required):
```bash
# Enable demo mode in .env
echo "DEMO_MODE=true" >> .env

# Start with Docker Compose
docker compose -f docker/docker-compose.yml up -d
```

In demo mode, the application uses synthetic data for 5 companies (AAPL, MSFT, GOOGL, AMZN, TSLA) and does not require any external API keys. All demo values are clearly labeled **[DEMO / SYNTHETIC DATA]**.

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

## Demo Mode Documentation

### Overview

Demo Mode provides a **fully self-contained demonstration path** for evaluators. When enabled, the application uses deterministic local fixtures instead of external APIs, allowing immediate demonstration of all major financial-analysis workflows without credentials.

### Enabling Demo Mode

```bash
# Option 1: Environment variable
export DEMO_MODE=true

# Option 2: .env file (persistent)
echo "DEMO_MODE=true" > .env
```

Then start the application normally:
```bash
uvicorn app.main:app --reload
```

### Demo Companies

| Ticker | Company | Sector | Key Characteristics |
|--------|---------|--------|---------------------|
| **AAPL** | Apple Inc. | Technology | High margin, strong cash flow, mature growth |
| **MSFT** | Microsoft Corp. | Technology | Cloud leader, recurring revenue, low debt |
| **GOOGL** | Alphabet Inc. | Technology | Advertising dominant, cloud growing, cash rich |
| **AMZN** | Amazon.com Inc. | Consumer Cyclical | High revenue, thin retail margins, AWS profit engine |
| **TSLA** | Tesla Inc. | Consumer Cyclical | High growth, volatile, capital intensive |

### Functionality Demonstrated

| Workflow | Demo Support | Notes |
|----------|-------------|-------|
| Company Profile | ✅ | Name, sector, industry, market cap, description |
| Market Quotes | ✅ | Price, volume, beta, P/E, 52-week range |
| Financial Statements | ✅ | Income, Balance Sheet, Cash Flow (in $M) |
| Key Ratios | ✅ | Profitability, liquidity, leverage, efficiency |
| Valuation (DCF) | ✅ | Intrinsic value, upside, recommendation |
| Risk Analysis | ✅ | Piotroski F-Score, Altman Z-Score, Beneish M-Score |
| Financial Health | ✅ | Composite score with rating (STRONG/GOOD/WEAK) |
| Investment Recommendation | ✅ | BUY/HOLD/SELL with confidence |
| SEC Filings | ✅ | 10-K/10-Q metadata, accession numbers |
| RAG / Document Search | ✅ | Query synthetic filing sections |
| Chat / Q&A | ✅ | Ask questions about demo filings |

### Determinism Guarantees

- **Fixed values**: All prices, financials, and scores are static
- **No network calls**: Zero external dependencies in demo mode
- **Stable results**: Identical queries produce identical responses
- **No timestamps**: Demo data uses fixed dates (2024-12-31)

### Data Labeling

All demo data is explicitly labeled:
- Company names: `Apple Inc. [DEMO / SYNTHETIC DATA]`
- Filing text chunks: `[DEMO / SYNTHETIC DATA] Apple Inc. 2024 Form 10-K...`
- UI badges: **"DEMO MODE"** indicator in status bar, **"Synthetic Data"** badges
- Version endpoint: `GET /version` returns `"demo_mode": true`

### Switching Back to Production Mode

```bash
# Disable demo mode
echo "DEMO_MODE=false" > .env

# Or remove the line from .env (defaults to false)
# Then configure real API keys per Configuration section above
```

### Technical Implementation

Demo mode is implemented via **existing provider abstractions**:
- `DemoMarketProvider` → implements `MarketDataProvider` interface
- `DemoFinancialDataService` → replaces `FinancialDataService` 
- `DemoSECService` → replaces `SECService`
- `MemoryVectorStore` → replaces `QdrantStore` (pre-populated with demo embeddings)

**No scattered `if demo_mode` conditionals** — services auto-select implementations via Settings.

### Examiner Checklist

- [ ] `DEMO_MODE=true` in `.env`
- [ ] Backend starts: `uvicorn app.main:app --reload`
- [ ] Frontend starts: `cd frontend && npm run dev`
- [ ] Version endpoint shows `"demo_mode": true`
- [ ] Status bar shows **"DEMO MODE"** amber badge
- [ ] Analysis page for AAPL loads with synthetic data badges
- [ ] Valuation shows intrinsic value & recommendation
- [ ] Risk page shows Piotroski/Altman/Beneish scores
- [ ] Search/Chat returns results from demo filings
- [ ] No external API keys configured
- [ ] No Qdrant/Redis required

## Evaluation

The project includes a quantitative evaluation module for verifying the financial calculation engines.

### `app/evaluation/run.py` — Synthetic Reference Evaluation

Runs a deterministic evaluation of the core financial calculation engines (Piotroski F-Score, Altman Z-Score, Beneish M-Score, DCF Valuation) against independently defined expected reference values from complete synthetic multi-period financial data.

**Purpose:** Validates that calculation engines are correctly wired, produce numerically stable outputs, and match expected results for known synthetic inputs. This is a **synthetic reference evaluation** — it does not measure live predictive accuracy or real-world financial performance.

**Usage:**

```bash
# Run evaluation
python -m app.evaluation.run
```

**Output:** The evaluation prints a per-ticker, per-metric comparison showing calculated vs. reference values, relative error percentages, and pass/fail status (using a configurable tolerance, default 5%). A JSON summary is also printed for programmatic consumption.

**Example Output:**

```
======================================================================
FINANCIAL CALCULATION ENGINES — SYNTHETIC REFERENCE EVALUATION
======================================================================
Mode: REFERENCE EVALUATION (complete synthetic multi-period data)
Purpose: Verify calculation engines produce expected values
Data:  SYNTHETIC / REFERENCE — NOT LIVE MARKET DATA
======================================================================

Evaluating AAPL...
  piotroski_score                calc=      7.0000 ref=      7.0000 rel_err=  0.00% [PASS]
  altman_score                   calc=      8.1227 ref=      8.1227 rel_err=  0.00% [PASS]
  beneish_score                  calc=     -2.7020 ref=     -2.7020 rel_err=  0.00% [PASS]
  dcf_intrinsic_value            calc=     93.9189 ref=     93.9189 rel_err=  0.00% [PASS]
...

SUMMARY
======================================================================
  AAPL  : 4/4 passed (100.0%)
  MSFT  : 4/4 passed (100.0%)
  GOOGL : 4/4 passed (100.0%)
  AMZN  : 4/4 passed (100.0%)
  TSLA  : 4/4 passed (100.0%)
  OVERALL: 20/20 passed (100.0%)

NOTE: This evaluation uses SYNTHETIC multi-period reference data.
      It validates engine wiring and numerical stability, NOT live accuracy.
======================================================================
```

**Key Metrics Evaluated:**
- **Piotroski F-Score** (0-9): Financial strength indicator
- **Altman Z-Score**: Bankruptcy risk predictor
- **Beneish M-Score**: Earnings manipulation detector
- **DCF Intrinsic Value**: Discounted cash flow valuation per share

**Evaluation Fixtures:** Complete synthetic multi-period financial data (current + prior period) for 5 companies (AAPL, MSFT, GOOGL, AMZN, TSLA) with independently computed expected results in `app/evaluation/fixtures.py`.

## License

See [LICENSE](LICENSE) for details.
