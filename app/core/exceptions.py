from __future__ import annotations
from typing import Any
class FinancialAnalystError(Exception):
    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        *,
        error_code: str = "GENERIC_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.details: dict[str, Any] = details if details is not None else {}
        super().__init__(self.message)
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"details={self.details!r})"
        )
    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "exception_type": self.__class__.__name__,
        }
class ConfigurationError(FinancialAnalystError):
    def __init__(
        self,
        message: str = "Configuration error.",
        *,
        error_code: str = "CONFIG_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)
class ValidationError(FinancialAnalystError):
    def __init__(
        self,
        message: str = "Validation error.",
        *,
        error_code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)
class RetrievalError(FinancialAnalystError):
    def __init__(
        self,
        message: str = "Data retrieval error.",
        *,
        error_code: str = "RETRIEVAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)
class ParserError(FinancialAnalystError):
    def __init__(
        self,
        message: str = "Document parsing error.",
        *,
        error_code: str = "PARSER_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)
class SandboxError(FinancialAnalystError):
    def __init__(
        self,
        message: str = "Sandbox execution error.",
        *,
        error_code: str = "SANDBOX_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)
class QuotaExceededError(FinancialAnalystError):
    def __init__(
        self,
        message: str = "Usage quota exceeded.",
        *,
        error_code: str = "QUOTA_EXCEEDED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)