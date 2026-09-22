from __future__ import annotations
from typing import Any
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.exceptions import (
    ConfigurationError,
    FinancialAnalystError,
    ParserError,
    QuotaExceededError,
    RetrievalError,
    SandboxError,
    ValidationError,
)
from app.auth.exceptions import (
    AuthenticationError,
    AuthorizationError,
    EmailAlreadyRegisteredError,
)
from app.core.logging import get_logger
from app.schemas.base import APIResponse, ErrorDetail
logger = get_logger("app.api.exceptions")
_EXCEPTION_STATUS_MAP: dict[type[Exception], int] = {
    ConfigurationError: 500,
    ValidationError: 422,
    RetrievalError: 502,
    ParserError: 422,
    SandboxError: 400,
    QuotaExceededError: 429,
}
def _get_status_code_for_domain_error(exc: FinancialAnalystError) -> int:
    for exc_type, status_code in _EXCEPTION_STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return status_code
    return 500
async def financial_anyst_error_handler(
    request: Request,
    exc: FinancialAnalystError,
) -> JSONResponse:
    status_code = _get_status_code_for_domain_error(exc)
    logger.warning(
        "Domain exception: %s (code=%s) | %s %s | %d",
        exc.__class__.__name__,
        exc.error_code,
        request.method,
        request.url.path,
        status_code,
    )
    error_detail = ErrorDetail(
        message=exc.message,
        code=exc.error_code,
    )
    response = APIResponse.error_response(
        message=exc.message,
        errors=[error_detail],
    )
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode="json"),
    )
async def auth_error_handler(
    request: Request,
    exc: AuthenticationError | AuthorizationError | EmailAlreadyRegisteredError,
) -> JSONResponse:
    if isinstance(exc, EmailAlreadyRegisteredError):
        status_code = 409
    elif isinstance(exc, AuthorizationError):
        status_code = 403
    else:
        status_code = 401
    logger.warning(
        "Auth exception: %s (code=%s) | %s %s | %d",
        exc.__class__.__name__,
        exc.error_code,
        request.method,
        request.url.path,
        status_code,
    )
    error_detail = ErrorDetail(
        message=exc.message,
        code=exc.error_code,
    )
    response = APIResponse.error_response(
        message=exc.message,
        errors=[error_detail],
    )
    headers = (
        {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
    )
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(mode="json"),
        headers=headers,
    )
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.warning(
        "Validation error: %s %s | %s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    errors: list[ErrorDetail] = []
    for error in exc.errors():
        loc: tuple[Any, ...] = error.get("loc", ())
        field: str = ".".join(str(part) for part in loc if part != "body") or None
        errors.append(
            ErrorDetail(
                field=field,
                message=error.get("msg", "Validation error"),
                code=error.get("type"),
            )
        )
    response = APIResponse.error_response(
        message="Request validation failed",
        errors=errors,
    )
    return JSONResponse(
        status_code=422,
        content=response.model_dump(mode="json"),
    )
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    logger.info(
        "HTTP exception: %s %s | %d",
        request.method,
        request.url.path,
        exc.status_code,
    )
    error_detail = ErrorDetail(
        message=str(exc.detail),
        code=f"HTTP_{exc.status_code}",
    )
    response = APIResponse.error_response(
        message=str(exc.detail),
        errors=[error_detail],
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=response.model_dump(mode="json"),
        headers=exc.headers,
    )
async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled exception: %s %s | %s: %s",
        request.method,
        request.url.path,
        exc.__class__.__name__,
        str(exc),
    )
    error_detail = ErrorDetail(
        message="An internal server error occurred. Please try again later.",
        code="INTERNAL_ERROR",
    )
    response = APIResponse.error_response(
        message="An internal server error occurred.",
        errors=[error_detail],
    )
    return JSONResponse(
        status_code=500,
        content=response.model_dump(mode="json"),
    )
def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(FinancialAnalystError, financial_anyst_error_handler)
    app.add_exception_handler(AuthenticationError, auth_error_handler)
    app.add_exception_handler(AuthorizationError, auth_error_handler)
    app.add_exception_handler(EmailAlreadyRegisteredError, auth_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)