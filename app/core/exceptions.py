"""
Custom Exception Hierarchy

This module defines the domain-specific exception hierarchy for the AI
Financial Analyst application. All application errors inherit from a single
base class (``FinancialAnalystError``), enabling callers to catch broad or
narrow categories of failures with a predictable interface.

Design Decisions:
    - **Single root exception**: ``FinancialAnalystError`` allows top-level
      error handlers (e.g., FastAPI exception handlers) to catch all
      domain errors in one ``except`` block while still distinguishing
      subtypes when needed.
    - **Structured error metadata**: Every exception carries an ``error_code``
      (machine-readable) and optional ``details`` dict, making it trivial to
      serialize errors into JSON API responses or log entries.
    - **Open/Closed Principle**: New error categories subclass the base
      without modifying existing code. Each layer (config, retrieval,
      parsing, sandbox) has its own dedicated exception type.
    - **No third-party dependencies**: The hierarchy relies only on the
      standard library, keeping the core layer framework-agnostic.

Usage Example:
    >>> from app.core.exceptions import ParserError
    >>> raise ParserError(
    ...     message="Failed to parse 10-K filing: invalid XBRL structure",
    ...     error_code="PARSE_001",
    ...     details={"filing_id": "0001193125-24-123456", "section": "Cash Flow"},
    ... )
"""

from __future__ import annotations

from typing import Any


class FinancialAnalystError(Exception):
    """
    Base exception for all application-specific errors.

    All custom exceptions in the AI Financial Analyst project inherit from
    this class. This allows application-wide error handling (logging,
    FastAPI exception handlers, retry logic) to catch a single root type.

    Attributes:
        message: Human-readable description of the error.
        error_code: Machine-readable error code for programmatic handling
            (e.g., ``"CONFIG_001"``). Defaults to ``"GENERIC_ERROR"``.
        details: Optional dictionary of additional context (e.g., filing IDs,
            HTTP status codes, field names). Defaults to an empty dict.
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        *,
        error_code: str = "GENERIC_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: Human-readable description of the error.
            error_code: Machine-readable error code for programmatic handling.
            details: Optional dictionary of additional context.
        """
        self.message = message
        self.error_code = error_code
        self.details: dict[str, Any] = details if details is not None else {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return a human-readable string representation of the error."""
        return f"[{self.error_code}] {self.message}"

    def __repr__(self) -> str:
        """Return an unambiguous developer-facing representation."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"details={self.details!r})"
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the exception to a dictionary.

        Useful for converting exceptions into JSON API error responses
        or structured log entries.

        Returns:
            A dictionary with ``error_code``, ``message``, ``details``,
            and ``exception_type`` keys.
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "exception_type": self.__class__.__name__,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Configuration Errors
# ──────────────────────────────────────────────────────────────────────────────


class ConfigurationError(FinancialAnalystError):
    """
    Raised when application configuration is invalid or incomplete.

    This includes missing required environment variables, invalid values,
    or failure to load the ``.env`` file.

    Example:
        >>> raise ConfigurationError(
        ...     message="OPENAI_API_KEY is not set",
        ...     error_code="CONFIG_001",
        ... )
    """

    def __init__(
        self,
        message: str = "Configuration error.",
        *,
        error_code: str = "CONFIG_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the configuration error."""
        super().__init__(message, error_code=error_code, details=details)


# ──────────────────────────────────────────────────────────────────────────────
# Validation Errors
# ──────────────────────────────────────────────────────────────────────────────


class ValidationError(FinancialAnalystError):
    """
    Raised when input data fails domain-level validation.

    This is used for business-rule violations that go beyond Pydantic's
    schema validation (e.g., a filing date is in the future, or a ticker
    symbol does not match the expected pattern).

    Example:
        >>> raise ValidationError(
        ...     message="Ticker symbol must be 1-5 uppercase letters",
        ...     error_code="VAL_001",
        ...     details={"field": "ticker", "value": "invalidticker123"},
        ... )
    """

    def __init__(
        self,
        message: str = "Validation error.",
        *,
        error_code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the validation error."""
        super().__init__(message, error_code=error_code, details=details)


# ──────────────────────────────────────────────────────────────────────────────
# Retrieval Errors
# ──────────────────────────────────────────────────────────────────────────────


class RetrievalError(FinancialAnalystError):
    """
    Raised when data retrieval from an external source fails.

    This covers errors from SEC EDGAR, Financial Modeling Prep, vector
    store queries, or any data-fetching operation.

    Example:
        >>> raise RetrievalError(
        ...     message="SEC EDGAR returned HTTP 429: Rate limit exceeded",
        ...     error_code="RETR_001",
        ...     details={"url": "https://efts.sec.gov/...", "status_code": 429},
        ... )
    """

    def __init__(
        self,
        message: str = "Data retrieval error.",
        *,
        error_code: str = "RETRIEVAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the retrieval error."""
        super().__init__(message, error_code=error_code, details=details)


# ──────────────────────────────────────────────────────────────────────────────
# Parser Errors
# ──────────────────────────────────────────────────────────────────────────────


class ParserError(FinancialAnalystError):
    """
    Raised when parsing a financial document fails.

    This includes errors in XBRL/HTML parsing, unexpected document
    structure, or failure to extract required financial data sections.

    Example:
        >>> raise ParserError(
        ...     message="Could not locate 'Income Statement' section in 10-K",
        ...     error_code="PARSE_002",
        ...     details={"filing_type": "10-K", "accession": "0001193125-24-123456"},
        ... )
    """

    def __init__(
        self,
        message: str = "Document parsing error.",
        *,
        error_code: str = "PARSER_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the parser error."""
        super().__init__(message, error_code=error_code, details=details)


# ──────────────────────────────────────────────────────────────────────────────
# Sandbox Errors
# ──────────────────────────────────────────────────────────────────────────────


class SandboxError(FinancialAnalystError):
    """
    Raised when sandboxed code execution fails or violates constraints.

    This includes timeouts, memory-limit violations, syntax errors in
    user-submitted code, or unauthorized operations within the sandbox.

    Example:
        >>> raise SandboxError(
        ...     message="Sandbox execution timed out after 30 seconds",
        ...     error_code="SBOX_001",
        ...     details={"timeout_seconds": 30, "code_snippet": "..."},
        ... )
    """

    def __init__(
        self,
        message: str = "Sandbox execution error.",
        *,
        error_code: str = "SANDBOX_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the sandbox error."""
        super().__init__(message, error_code=error_code, details=details)