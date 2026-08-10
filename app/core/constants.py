"""
Centralized Application Constants

This module serves as the single source of truth for all constant values
used throughout the AI Financial Analyst application. By centralizing
constants, we eliminate "magic numbers" and hardcoded strings scattered
across the codebase, improving maintainability and reducing errors.

Design Decisions:
    - **Enums for categorical values**: Environments, filing types, and log
      levels use ``enum.Enum`` to provide type safety, IDE autocompletion,
      and exhaustive ``match`` checks.
    - ``typing.Final`` for scalar constants: Signals immutability to type
      checkers (mypy) and documents intent.
    - **No business logic**: This module contains only data declarations.
      Functions and methods belong in their respective service modules.

References:
    - PEP 591: https://peps.python.org/pep-0591/  (``Final`` qualifier)
    - PEP 435: https://peps.python.org/pep-0435/  (``enum`` module)
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final

# ──────────────────────────────────────────────────────────────────────────────
# Application Metadata
# ──────────────────────────────────────────────────────────────────────────────

APP_NAME: Final[str] = "AI Financial Analyst"
"""Human-readable application name displayed in logs and UIs."""

APP_VERSION: Final[str] = "0.1.0"
"""Semantic version of the application (PEP 440 compliant)."""

# ──────────────────────────────────────────────────────────────────────────────
# Environment
# ──────────────────────────────────────────────────────────────────────────────


class Environment(StrEnum):
    """
    Supported deployment environments.

    The environment controls configuration loading, logging verbosity, and
    feature toggles. It is read from the ``ENVIRONMENT`` variable in ``.env``.

    Members:
        DEVELOPMENT: Local development with verbose logging and debug tools.
        STAGING: Pre-production mirror for integration testing.
        PRODUCTION: Live deployment with hardened security and minimal logs.
        TEST: Automated test runs with isolated resources.
    """

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────


class LogLevel(StrEnum):
    """
    Standard Python logging levels as enum members.

    Using an ``enum`` instead of raw ``int`` constants from ``logging`` keeps
    configuration type-safe and serializable via Pydantic Settings.

    Members:
        DEBUG: Detailed diagnostic information (development only).
        INFO: General operational events confirming normal progress.
        WARNING: Exceptional but non-fatal conditions requiring attention.
        ERROR: Errors that prevented an operation from completing.
        CRITICAL: Severe errors that may force application shutdown.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


LOG_DIR: Final[str] = "storage/logs"
"""Directory where rotating log files are persisted."""

LOG_FILE_NAME: Final[str] = "app.log"
"""Base name of the main application log file."""

LOG_MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB
"""Maximum size of a single log file before rotation occurs (in bytes)."""

LOG_BACKUP_COUNT: Final[int] = 5
"""Number of rotated backup log files to retain."""

LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
"""``strftime`` pattern used for timestamps in log entries."""

LOG_FILE_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
)
"""Format string for file-based log records (verbose, machine-parseable)."""

LOG_CONSOLE_FORMAT: Final[str] = "%(message)s"
"""Format string for console log records (Rich handles styling)."""

# ──────────────────────────────────────────────────────────────────────────────
# API & Network
# ──────────────────────────────────────────────────────────────────────────────

API_DEFAULT_TIMEOUT: Final[int] = 30
"""Default HTTP request timeout in seconds."""

API_MAX_RETRIES: Final[int] = 3
"""Maximum number of retry attempts for failed HTTP requests."""

API_RETRY_BACKOFF: Final[float] = 0.5
"""Base delay (seconds) for exponential backoff between retries."""

API_RETRY_STATUS_CODES: Final[tuple[int, ...]] = (429, 500, 502, 503, 504)
"""HTTP status codes that should trigger a retry."""

# ──────────────────────────────────────────────────────────────────────────────
# External Service Endpoints
# ──────────────────────────────────────────────────────────────────────────────

SEC_API_BASE_URL: Final[str] = "https://www.sec.gov/cgi-bin/browse"
"""Base URL for SEC EDGAR public filings search."""

SEC_FULL_TEXT_SEARCH_URL: Final[str] = "https://efts.sec.gov/LATEST/search-index"
"""Base URL for SEC EDGAR full-text search API."""

FMP_API_BASE_URL: Final[str] = "https://financialmodelingprep.com/api/v3"
"""Base URL for Financial Modeling Prep (FMP) REST API."""

OPENAI_API_BASE_URL: Final[str] = "https://api.openai.com/v1"
"""Base URL for OpenAI REST API."""

# ──────────────────────────────────────────────────────────────────────────────
# Database
# ──────────────────────────────────────────────────────────────────────────────

DB_POOL_SIZE: Final[int] = 10
"""Default connection pool size for the primary database."""

DB_MAX_OVERFLOW: Final[int] = 20
"""Maximum overflow connections beyond the pool size."""

DB_POOL_TIMEOUT: Final[int] = 30
"""Seconds to wait for a connection before timing out."""

DB_POOL_RECYCLE: Final[int] = 3600
"""Seconds after which a pooled connection is recycled (1 hour)."""

# ──────────────────────────────────────────────────────────────────────────────
# Financial Document / Filing Types
# ──────────────────────────────────────────────────────────────────────────────


class FilingType(StrEnum):
    """
    SEC filing types supported by the ingestion and parsing pipelines.

    Each member's value matches the official SEC EDGAR form type identifier,
    ensuring compatibility with EDGAR search queries and filing metadata.

    Members:
        FORM_10K: Annual report (Form 10-K).
        FORM_10Q: Quarterly report (Form 10-Q).
        FORM_8K: Current report (Form 8-K).
        FORM_20F: Annual report of foreign private issuer (Form 20-F).
        FORM_S1: Registration statement (Form S-1).
        FORM_DEF14A: Definitive proxy statement (DEF 14A).
        FORM_13F: Institutional investment manager report (13F-HR).
        FORM_13D: Beneficial ownership report (Schedule 13D).
        FORM_13G: Beneficial ownership report (Schedule 13G).
        FORM_4: Statement of changes in beneficial ownership (Form 4).
    """

    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    FORM_20F = "20-F"
    FORM_S1 = "S-1"
    FORM_DEF14A = "DEF 14A"
    FORM_13F = "13F-HR"
    FORM_13D = "SC 13D"
    FORM_13G = "SC 13G"
    FORM_4 = "4"


SUPPORTED_FILING_TYPES: Final[frozenset[str]] = frozenset(
    {filing.value for filing in FilingType}
)
"""Immutable set of all supported filing type identifiers (e.g., ``"10-K"``)."""

# ──────────────────────────────────────────────────────────────────────────────
# Financial Document Sections
# ──────────────────────────────────────────────────────────────────────────────

FINANCIAL_STATEMENT_SECTIONS: Final[tuple[str, ...]] = (
    "Income Statement",
    "Balance Sheet",
    "Cash Flow Statement",
    "Statement of Stockholders' Equity",
    "Notes to Financial Statements",
)
"""Standard sections found in SEC annual and quarterly filings."""

KEY_FINANCIAL_METRICS: Final[tuple[str, ...]] = (
    "Total Revenue",
    "Gross Profit",
    "Operating Income",
    "Net Income",
    "Earnings Per Share (EPS)",
    "EBITDA",
    "Total Assets",
    "Total Liabilities",
    "Total Stockholders' Equity",
    "Operating Cash Flow",
    "Free Cash Flow",
    "Debt-to-Equity Ratio",
    "Current Ratio",
    "Return on Equity (ROE)",
    "Return on Assets (ROA)",
)
"""Key financial metrics extracted from filings for analysis."""

# ──────────────────────────────────────────────────────────────────────────────
# Sandbox (Code Execution)
# ──────────────────────────────────────────────────────────────────────────────

SANDBOX_TIMEOUT: Final[int] = 30
"""Maximum wall-clock seconds a sandboxed code execution may run."""

SANDBOX_MEMORY_LIMIT_MB: Final[int] = 512
"""Maximum memory (MB) a sandboxed process may allocate."""

SANDBOX_CPU_LIMIT: Final[float] = 1.0
"""CPU core limit for sandboxed processes (1.0 = one full core)."""

# ──────────────────────────────────────────────────────────────────────────────
# Retrieval / Vector Store
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_EMBEDDING_MODEL: Final[str] = "text-embedding-3-small"
"""Default OpenAI embedding model for document vectorization."""

DEFAULT_VECTOR_TOP_K: Final[int] = 5
"""Default number of chunks retrieved per query in vector search."""

DEFAULT_ENABLE_RERANKER: Final[bool] = False
"""Whether the cross-encoder reranker runs after hybrid retrieval."""

DEFAULT_CHUNK_SIZE: Final[int] = 1000
"""Default character length of text chunks during ingestion."""

DEFAULT_CHUNK_OVERLAP: Final[int] = 200
"""Default overlap (characters) between adjacent text chunks."""

# ──────────────────────────────────────────────────────────────────────────────
# LLM / Agent
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_LLM_MODEL: Final[str] = "gpt-4o"
"""Default OpenAI chat completion model for analytical agents."""

DEFAULT_LLM_TEMPERATURE: Final[float] = 0.0
"""Default sampling temperature (0.0 = deterministic, for financial accuracy)."""

DEFAULT_LLM_MAX_TOKENS: Final[int] = 4096
"""Default maximum tokens generated per LLM response."""

# ──────────────────────────────────────────────────────────────────────────────
# File Paths & Storage
# ──────────────────────────────────────────────────────────────────────────────

STORAGE_ROOT: Final[str] = "storage"
"""Root directory for all persistent application storage."""

RAW_DATA_DIR: Final[str] = "storage/raw"
"""Directory for raw downloaded filings before parsing."""

PARSED_DATA_DIR: Final[str] = "storage/parsed"
"""Directory for parsed/structured filing output."""

EMBEDDINGS_DIR: Final[str] = "storage/embeddings"
"""Directory for vector embeddings and vector store indices."""

CONFIGS_DIR: Final[str] = "configs"
"""Directory for YAML/JSON configuration files."""