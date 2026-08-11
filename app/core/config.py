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
    DEFAULT_VECTOR_TOP_K,
    SANDBOX_MEMORY_LIMIT_MB,
    SANDBOX_TIMEOUT,
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

    def validate_required_keys(self) -> None:
        """Validate that required API keys are set for non-test environments."""
        if self.environment == Environment.TEST:
            return

        missing: list[str] = []

        if not self.openai_api_key_str:
            missing.append("OPENAI_API_KEY")

        if self.is_production and not self.fmp_api_key_str:
            missing.append("FMP_API_KEY")

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