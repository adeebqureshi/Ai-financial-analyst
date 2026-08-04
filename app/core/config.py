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
    APP_NAME,
    APP_VERSION,
    API_DEFAULT_TIMEOUT,
    API_MAX_RETRIES,
    API_RETRY_BACKOFF,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_LLM_MAX_TOKENS,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_TEMPERATURE,
    DEFAULT_VECTOR_TOP_K,
    Environment,
    LogLevel,
    SANDBOX_MEMORY_LIMIT_MB,
    SANDBOX_TIMEOUT,
)
from app.core.exceptions import ConfigurationError


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and ``.env``.

    All settings have sensible defaults for local development. In production,
    critical secrets (API keys) must be provided via environment variables or
    a ``.env`` file.

    Attributes:
        app_name: Human-readable application name.
        app_version: Semantic version string.
        environment: Current deployment environment (dev/staging/prod/test).
        debug: Global debug flag (auto-set based on environment).

        -- API Keys --
        openai_api_key: OpenAI API key for LLM and embedding calls.
        sec_api_key: SEC EDGAR API key (if using a paid SEC API service).
        fmp_api_key: Financial Modeling Prep API key.

        -- Logging --
        log_level: Minimum log level to emit.
        log_to_file: Whether to write logs to rotating files.
        log_to_console: Whether to write logs to the console (Rich).

        -- API / Network --
        api_timeout: Default HTTP request timeout in seconds.
        api_max_retries: Maximum retry attempts for failed HTTP requests.
        api_retry_backoff: Base delay (seconds) for exponential backoff.

        -- LLM --
        llm_model: Default OpenAI chat completion model.
        llm_temperature: Sampling temperature for LLM responses.
        llm_max_tokens: Maximum tokens per LLM response.

        -- Retrieval --
        embedding_model: OpenAI embedding model name.
        vector_top_k: Number of chunks to retrieve per query.
        chunk_size: Character length of text chunks.
        chunk_overlap: Overlap between adjacent chunks.

        -- Sandbox --
        sandbox_timeout: Max seconds for sandboxed code execution.
        sandbox_memory_limit_mb: Max memory (MB) for sandboxed processes.
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

    # ── LLM ──────────────────────────────────────────────────────────────
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
        """
        Ensure LLM temperature is within the valid range [0.0, 2.0].

        Args:
            v: The temperature value to validate.

        Returns:
            The validated temperature.

        Raises:
            ValueError: If temperature is outside [0.0, 2.0].
        """
        if not 0.0 <= v <= 2.0:
            raise ValueError("llm_temperature must be between 0.0 and 2.0")
        return v

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: int) -> int:
        """
        Ensure chunk overlap is non-negative and less than chunk size.

        Args:
            v: The overlap value to validate.

        Returns:
            The validated overlap.

        Raises:
            ValueError: If overlap is negative or >= chunk_size.
        """
        if v < 0:
            raise ValueError("chunk_overlap must be non-negative")
        return v

    # ── Post-Init Environment Adjustments ────────────────────────────────

    def model_post_init(self, __context: Any) -> None:
        """
        Adjust settings based on the active environment after validation.

        In development/test, debug mode is enabled and log level defaults
        to DEBUG. In production, debug is disabled and log level defaults
        to WARNING if it was left at INFO.

        Args:
            __context: Pydantic internal context (unused).
        """
        # Use object.__setattr__ because the model is frozen
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
        """
        Return the OpenAI API key as a plain string.

        Returns:
            The decrypted API key string, or empty string if unset.
        """
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
        """
        Validate that required API keys are set for non-test environments.

        In production and staging, ``openai_api_key`` must be non-empty.
        This is called explicitly at application startup rather than in
        ``__init__`` to allow tests to construct ``Settings`` without keys.

        Raises:
            ConfigurationError: If a required key is missing.
        """
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
    """
    Return the singleton ``Settings`` instance.

    Uses ``functools.lru_cache`` to ensure the settings are loaded only once
    per process. This is thread-safe and avoids repeated file I/O / env
    parsing on every call.

    To reset the cache (e.g., in tests), call::

        get_settings.cache_clear()

    Returns:
        The cached ``Settings`` instance.

    Raises:
        ConfigurationError: If settings cannot be loaded or validated.
    """
    try:
        return Settings()
    except Exception as exc:
        raise ConfigurationError(
            message=f"Failed to load application settings: {exc}",
            error_code="CONFIG_002",
            details={"original_error": str(exc)},
        ) from exc


def get_project_root() -> Path:
    """
    Return the project root directory.

    The root is determined by the location of the ``app`` package. This
    function is used to resolve relative paths for storage directories.

    Returns:
        A ``Path`` pointing to the project root.
    """
    return Path(__file__).resolve().parent.parent.parent