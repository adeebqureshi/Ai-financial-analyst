"""
Application Configuration

This module defines the application's configuration system using
``pydantic-settings``. It reads settings from environment variables and
a ``.env`` file, validates them, and exposes a thread-safe singleton
instance via ``get_settings()``.

Design Decisions:
    - **Pydantic Settings over ``os.environ``**: Provides type validation,
      default values, nested config, and ``.env`` file support out of the
      box. Invalid values raise ``ValidationError`` at startup, failing
      fast rather than at runtime.
    - **Singleton via ``lru_cache``**: ``functools.lru_cache`` ensures the
      ``Settings`` object is instantiated only once per process, is
      thread-safe, and can be reset in tests via ``get_settings.cache_clear()``.
    - **Environment-aware defaults**: The ``model_post_init`` hook adjusts
      logging verbosity and debug flags based on the active environment
      (development vs. production), reducing the number of variables
      developers must set explicitly.
    - **Secrets handling**: API keys are typed as ``SecretStr`` to prevent
      accidental logging or serialization of sensitive values.
    - **Immutability**: ``model_config = SettingsConfigDict(frozen=True)``
      prevents runtime mutation of configuration, eliminating a class of
      concurrency bugs.

Usage:
    >>> from app.core.config import get_settings
    >>> settings = get_settings()
    >>> print(settings.app_name)
    AI Financial Analyst
    >>> print(settings.environment)
    Environment.DEVELOPMENT
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import (
    API_DEFAULT_TIMEOUT,
    API_MAX_RETRIES,
    API_RETRY_BACKOFF,
    APP_NAME,
    APP_VERSION,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_ENABLE_RERANKER,
    DEFAULT_LLM_MAX_TOKENS,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_TEMPERATURE,
    DEFAULT_LLM_TOKEN_QUOTA_PER_USER_PER_DAY,
    DEFAULT_PROJECTION_YEARS,
    DEFAULT_RISK_FREE_RATE,
    DEFAULT_MARKET_RETURN,
    DEFAULT_COST_OF_DEBT,
    DEFAULT_TAX_RATE,
    DEFAULT_TERMINAL_GROWTH,
    DEFAULT_VECTOR_TOP_K,
    SANDBOX_MEMORY_LIMIT_MB,
    SANDBOX_TIMEOUT,
    DEFAULT_MARKET_FALLBACK_PROVIDERS,
    DEFAULT_MARKET_PRIMARY_PROVIDER,

    Environment,
    LogLevel,
)
from app.core.exceptions import ConfigurationError


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and ``.env``.

    All settings have sensible defaults for local development. In production,
    critical secrets (API keys) must be provided via environment variables or
    a ``.env`` file.
    """

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = Field(default=APP_NAME, description="Application name.")
    app_version: str = Field(default=APP_VERSION, description="Application version.")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment.",
    )
    debug: bool = Field(default=False, description="Enable debug mode.")

    # ── API Keys ─────────────────────────────────────────────────────────
    openai_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="OpenAI API key.",
    )
    sec_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="SEC EDGAR API key.",
    )
    fmp_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Financial Modeling Prep API key.",
    )
    llama_parse_api_key: SecretStr = Field(
        default=SecretStr(""),
        description=(
            "LlamaParse API key. Optional: enables layout-aware Markdown PDF "
            "parsing. Without it the pipeline falls back to Marker/PyMuPDF."
        ),
    )

    # ── Logging ──────────────────────────────────────────────────────────
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Minimum log level.")
    log_to_file: bool = Field(default=True, description="Enable file logging.")
    log_to_console: bool = Field(default=True, description="Enable console logging.")

    # ── API / Network ────────────────────────────────────────────────────
    api_timeout: int = Field(
        default=API_DEFAULT_TIMEOUT,
        description="HTTP request timeout in seconds.",
    )
    api_max_retries: int = Field(
        default=API_MAX_RETRIES,
        description="Maximum HTTP retry attempts.",
    )
    api_retry_backoff: float = Field(
        default=API_RETRY_BACKOFF,
        description="Base delay for exponential backoff (seconds).",
    )

    # ── Market Data Providers ────────────────────────────────────────────
    # NOTE: Yahoo Finance (via yfinance) is an unofficial, non-commercial-use
    # data source with no SLA. The provider chain is configuration-driven so
    # it can be replaced without changing business logic.
    market_primary_provider: str = Field(
        default=DEFAULT_MARKET_PRIMARY_PROVIDER,
        description=(
            "Primary market-data provider name. 'yahoo' (Yahoo Finance via "
            "yfinance) is the default — an unofficial, non-commercial-use "
            "source with no SLA; swap via this setting without code changes."
        ),
    )
    market_fallback_providers: str = Field(
        default=DEFAULT_MARKET_FALLBACK_PROVIDERS,
        description=(
            "Comma-separated fallback provider names tried in order when the "
            "primary fails (e.g. 'fmp'). Empty string disables fallback."
        ),
    )
    market_fallback_enabled: bool = Field(
        default=True,
        description="Enable the fallback provider chain.",
    )
    market_provider_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        description="Per-provider fetch timeout in seconds.",
    )
    market_provider_max_attempts: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Retry attempts per provider for transient errors.",
    )
    market_quote_ttl_seconds: int = Field(
        default=60,
        ge=0,
        description="Quote cache freshness TTL (seconds). 0 disables caching.",
    )
    market_cache_stale_seconds: int = Field(
        default=900,
        ge=0,
        description=(
            "Extra window (seconds) during which a cached quote may be "
            "served (flagged stale) when all providers fail. 0 disables "
            "stale serving."
        ),
    )
    market_cache_max_entries: int = Field(
        default=1024,
        ge=1,
        description="Max entries for the in-process quote cache (LRU).",
    )
    market_cache_backend: str = Field(
        default="auto",
        description="Quote cache backend: 'auto' (Redis else in-process), 'redis', or 'memory'.",
    )

    # ── Financial Assumptions (valuation inputs) ──────────────────────────
    # These are the canonical "macro" inputs to DCF/WACC valuation. They are
    # explicit assumptions, NOT live market data. Each carries a documented
    # default; override any of them to reflect a different view. See
    # ``app.financial.assumptions`` for the single source of truth and the
    # validation bounds applied at runtime.
    risk_free_rate: float = Field(
        default=DEFAULT_RISK_FREE_RATE,
        ge=0.0,
        le=0.5,
        description="Annual risk-free rate as a decimal (e.g. 0.0425 = 4.25%). Assumption, not live data.",
    )
    market_return: float = Field(
        default=DEFAULT_MARKET_RETURN,
        ge=0.0,
        le=1.0,
        description="Expected annual market return as a decimal (e.g. 0.10 = 10%). Assumption, not live data.",
    )
    cost_of_debt: float = Field(
        default=DEFAULT_COST_OF_DEBT,
        ge=0.0,
        le=1.0,
        description="Pre-tax cost of debt as a decimal (e.g. 0.05 = 5%). Assumption, not live data.",
    )
    tax_rate: float = Field(
        default=DEFAULT_TAX_RATE,
        ge=0.0,
        le=1.0,
        description="Effective tax rate as a decimal (e.g. 0.21 = 21%). Assumption, not live data.",
    )
    terminal_growth: float = Field(
        default=DEFAULT_TERMINAL_GROWTH,
        ge=0.0,
        le=0.2,
        description="Perpetual terminal growth rate as a decimal (e.g. 0.03 = 3%). Assumption, not live data.",
    )
    projection_years: int = Field(
        default=DEFAULT_PROJECTION_YEARS,
        ge=1,
        le=30,
        description="DCF projection horizon in whole years.",
    )

    # ── SEC EDGAR ────────────────────────────────────────────────────────
    edgar_identity: str = Field(
        default="",
        description="SEC EDGAR User-Agent identity.",
    )

    # ── LLM ──────────────────────────────────────────────────────────────
    llm_provider: str = Field(
        default="mock",
        description=(
            "LLM provider name used by OpenAIClient. Set to 'openai' (or any "
            "name registered in ProviderFactory) in production; 'mock' is the "
            "safe default for tests and offline development."
        ),
    )
    llm_model: str = Field(
        default=DEFAULT_LLM_MODEL,
        description="Default OpenAI chat completion model.",
    )
    llm_temperature: float = Field(
        default=DEFAULT_LLM_TEMPERATURE,
        description="LLM sampling temperature.",
    )
    llm_max_tokens: int = Field(
        default=DEFAULT_LLM_MAX_TOKENS,
        description="Maximum tokens per LLM response.",
    )
    llm_token_quota_per_user_per_day: int = Field(
        default=DEFAULT_LLM_TOKEN_QUOTA_PER_USER_PER_DAY,
        description=(
            "Maximum estimated LLM tokens (input + reserved output) an "
            "authenticated user may spend per day across chat endpoints. "
            "0 disables the quota. Unauthenticated requests remain covered "
            "by per-IP request rate limits."
        ),
    )

    # ── Retrieval / Vector Store ─────────────────────────────────────────
    embedding_model: str = Field(
        default=DEFAULT_EMBEDDING_MODEL,
        description="OpenAI embedding model name.",
    )
    vector_top_k: int = Field(
        default=DEFAULT_VECTOR_TOP_K,
        description="Number of chunks to retrieve per query.",
    )
    chunk_size: int = Field(
        default=DEFAULT_CHUNK_SIZE,
        description="Character length of text chunks.",
    )
    chunk_overlap: int = Field(
        default=DEFAULT_CHUNK_OVERLAP,
        description="Overlap between adjacent text chunks.",
    )
    enable_reranker: bool = Field(
        default=DEFAULT_ENABLE_RERANKER,
        description="Run the cross-encoder reranker after hybrid retrieval.",
    )

    # ── Sandbox ──────────────────────────────────────────────────────────
    sandbox_timeout: int = Field(
        default=SANDBOX_TIMEOUT,
        description="Max seconds for sandboxed code execution.",
    )
    sandbox_memory_limit_mb: int = Field(
        default=SANDBOX_MEMORY_LIMIT_MB,
        description="Max memory (MB) for sandboxed processes.",
    )

    # ── Authentication / Authorization ───────────────────────────────────
    auth_enabled: bool = Field(
        default=True,
        description=(
            "Require authentication on business endpoints. Secure by "
            "default; set AUTH_ENABLED=false only for trusted local "
            "development or legacy test harnesses."
        ),
    )
    auth_secret_key: SecretStr = Field(
        default=SecretStr(""),
        description=(
            "JWT signing secret. REQUIRED in production when auth is "
            "enabled; when empty an ephemeral process-random secret is "
            "used (tokens invalidate on restart)."
        ),
    )
    access_token_expire_minutes: int = Field(
        default=60,
        description="Lifetime of issued JWT access tokens, in minutes.",
    )
    auth_database_url: str = Field(
        default="sqlite:///./data/auth.db",
        description="SQLAlchemy URL for the user account store.",
    )

    # ── Chat Persistence ─────────────────────────────────────────────────
    chat_database_url: str = Field(
        default="sqlite:///./data/chat.db",
        description=(
            "SQLAlchemy URL for the chat conversation store. SQLite by "
            "default for local development; use PostgreSQL in production, "
            "e.g. postgresql+psycopg://user:pass@host/db."
        ),
    )
    chat_redis_url: str = Field(
        default="redis://localhost:6379/1",
        description=(
            "Optional Redis URL used to cache recent chat session context. "
            "When Redis is unavailable the store transparently falls back to "
            "the database."
        ),
    )
    chat_retention_days: int = Field(
        default=30,
        description=(
            "Retention window (days) after which idle chat sessions and their "
            "messages are purged by the retention/cleanup routine."
        ),
    )

    # ── Demo Mode ──────────────────────────────────────────────────────────
    demo_mode: bool = Field(
        default=False,
        description=(
            "Enable deterministic demo mode with synthetic data. When true, the "
            "application uses local demo fixtures instead of external APIs. "
            "NEVER enable in production. All demo values are clearly labeled "
            "as synthetic."
        ),
    )

    # ── CORS ───────────────────────────────────────────────────────────────
    cors_origins: str = Field(
        default="",
        description=(
            "Comma-separated list of allowed CORS origins for production. "
            "Required when ENVIRONMENT=production. "
            "Example: https://app.example.com,https://www.example.com. "
            "In development/test, localhost origins are added automatically."
        ),
    )

    # ── Rate Limiting ────────────────────────────────────────────────────
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting on expensive endpoints.",
    )
    rate_limit_redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for distributed rate limiting. Falls back to local memory when unavailable.",
    )
    rate_limit_default_per_minute: int = Field(
        default=60,
        description="Default requests per minute per user/IP.",
    )
    rate_limit_default_per_hour: int = Field(
        default=1000,
        description="Default requests per hour per user/IP.",
    )
    rate_limit_chat_per_minute: int = Field(
        default=20,
        description="Chat endpoint requests per minute per user/IP.",
    )
    rate_limit_chat_per_hour: int = Field(
        default=200,
        description="Chat endpoint requests per hour per user/IP.",
    )
    rate_limit_analyze_per_minute: int = Field(
        default=10,
        description="Analysis endpoint requests per minute per user/IP.",
    )
    rate_limit_analyze_per_hour: int = Field(
        default=100,
        description="Analysis endpoint requests per hour per user/IP.",
    )
    rate_limit_documents_per_minute: int = Field(
        default=10,
        description="Documents endpoint requests per minute per user/IP.",
    )
    rate_limit_documents_per_hour: int = Field(
        default=100,
        description="Documents endpoint requests per hour per user/IP.",
    )
    rate_limit_search_per_minute: int = Field(
        default=30,
        description="Search endpoint requests per minute per user/IP.",
    )
    rate_limit_search_per_hour: int = Field(
        default=300,
        description="Search endpoint requests per hour per user/IP.",
    )
    rate_limit_sandbox_per_minute: int = Field(
        default=5,
        description="Sandbox execution requests per minute per user/IP.",
    )
    rate_limit_sandbox_per_hour: int = Field(
        default=50,
        description="Sandbox execution requests per hour per user/IP.",
    )
    rate_limit_anonymous_multiplier: float = Field(
        default=0.1,
        description="Rate limit multiplier for anonymous requests (e.g., 0.1 = 10% of authenticated limits).",
    )

    # ── Pydantic Settings Configuration ──────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        frozen=True,
        extra="ignore",
    )

    # ── Validators ───────────────────────────────────────────────────────

    @field_validator("llm_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Ensure LLM temperature is within the valid range [0.0, 2.0]."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("llm_temperature must be between 0.0 and 2.0")
        return v

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: int) -> int:
        """Ensure chunk overlap is non-negative."""
        if v < 0:
            raise ValueError("chunk_overlap must be non-negative")
        return v

    @field_validator("access_token_expire_minutes")
    @classmethod
    def validate_token_expiry(cls, v: int) -> int:
        """Ensure access tokens have a positive, sane lifetime."""
        if not 1 <= v <= 24 * 60:
            raise ValueError(
                "access_token_expire_minutes must be between 1 and 1440"
            )
        return v

    # ── Post-Init Environment Adjustments ────────────────────────────────

    def model_post_init(self, __context: Any) -> None:
        """Adjust settings based on the active environment after validation."""
        if self.environment in (Environment.DEVELOPMENT, Environment.TEST):
            if not self.debug:
                object.__setattr__(self, "debug", True)
        else:
            object.__setattr__(self, "debug", False)

    # ── Helper Properties ────────────────────────────────────────────────

    @property
    def is_production(self) -> bool:
        """Return True if the current environment is production."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Return True if the current environment is development."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_test(self) -> bool:
        """Return True if the current environment is test."""
        return self.environment == Environment.TEST

    @property
    def is_demo_mode(self) -> bool:
        """Return True if demo mode is enabled."""
        return self.demo_mode

    @property
    def openai_api_key_str(self) -> str:
        """Return the OpenAI API key as a plain string."""
        return self.openai_api_key.get_secret_value()

    @property
    def sec_api_key_str(self) -> str:
        """Return the SEC API key as a plain string."""
        return self.sec_api_key.get_secret_value()

    @property
    def fmp_api_key_str(self) -> str:
        """Return the FMP API key as a plain string."""
        return self.fmp_api_key.get_secret_value()

    @property
    def llama_parse_api_key_str(self) -> str:
        """Return the LlamaParse API key as a plain string."""
        return self.llama_parse_api_key.get_secret_value()

    @property
    def auth_secret_key_str(self) -> str:
        """Return the JWT signing secret as a plain string."""
        return self.auth_secret_key.get_secret_value()

    def validate_required_keys(self) -> None:
        """Validate that required API keys are set for non-test environments."""
        if self.environment == Environment.TEST:
            return

        # Demo mode uses synthetic data and does not require external API keys.
        if self.is_demo_mode:
            return

        missing: list[str] = []

        if not self.openai_api_key_str:
            missing.append("OPENAI_API_KEY")

        if self.is_production and not self.fmp_api_key_str:
            missing.append("FMP_API_KEY")

        if self.is_production and self.auth_enabled and not self.auth_secret_key_str:
            missing.append("AUTH_SECRET_KEY")

        if missing:
            raise ConfigurationError(
                message=(
                    f"Required environment variables are not set: {', '.join(missing)}"
                ),
                error_code="CONFIG_001",
                details={"missing_keys": missing, "environment": str(self.environment)},
            )


# ──────────────────────────────────────────────────────────────────────────────
# Singleton Access
# ──────────────────────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton ``Settings`` instance."""
    try:
        return Settings()
    except Exception as exc:
        raise ConfigurationError(
            message=f"Failed to load application settings: {exc}",
            error_code="CONFIG_002",
            details={"original_error": str(exc)},
        ) from exc


settings = get_settings()


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent