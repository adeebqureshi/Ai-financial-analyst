from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
from rich.logging import RichHandler
from app.core.config import Settings, get_settings
from app.core.constants import (
    LOG_BACKUP_COUNT,
    LOG_CONSOLE_FORMAT,
    LOG_DATE_FORMAT,
    LOG_DIR,
    LOG_FILE_FORMAT,
    LOG_FILE_NAME,
    LOG_MAX_BYTES,
)
_LOGGING_CONFIGURED: bool = False
class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from app.infrastructure.request_id import get_request_id
            record.request_id = get_request_id()
        except Exception:
            record.request_id = "-"
        return True
def setup_logging(
    settings: Settings | None = None,
    *,
    force: bool = False,
) -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED and not force:
        return
    if settings is None:
        settings = get_settings()
    log_level: int = getattr(logging, settings.log_level.value, logging.INFO)
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)
    if settings.log_to_console:
        console_handler = RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=settings.debug,
            show_time=True,
            show_level=True,
            show_path=settings.debug,
        )
        console_handler.setLevel(log_level)
        console_handler.addFilter(RequestIDFilter())
        console_handler.setFormatter(logging.Formatter(LOG_CONSOLE_FORMAT, datefmt=LOG_DATE_FORMAT))
        root_logger.addHandler(console_handler)
    if settings.log_to_file:
        log_dir = Path(LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = log_dir / LOG_FILE_NAME
        file_handler = RotatingFileHandler(
            filename=str(log_file_path),
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.addFilter(RequestIDFilter())
        file_handler.setFormatter(
            logging.Formatter(LOG_FILE_FORMAT, datefmt=LOG_DATE_FORMAT)
        )
        root_logger.addHandler(file_handler)
    _configure_third_party_loggers(log_level)
    _LOGGING_CONFIGURED = True
    root_logger.debug(
        "Logging configured: level=%s, console=%s, file=%s",
        settings.log_level.value,
        settings.log_to_console,
        settings.log_to_file,
    )
def _configure_third_party_loggers(level: int) -> None:
    third_party_loggers: list[str] = [
        "httpx",
        "httpcore",
        "openai",
        "urllib3",
        "asyncio",
        "sentence_transformers",
    ]
    for name in third_party_loggers:
        logging.getLogger(name).setLevel(max(level, logging.WARNING))
def get_logger(name: str) -> logging.Logger:
    if not _LOGGING_CONFIGURED:
        setup_logging()
    return logging.getLogger(name)
def shutdown_logging() -> None:
    logging.shutdown()
    global _LOGGING_CONFIGURED
    _LOGGING_CONFIGURED = False
def get_log_file_path() -> Path:
    return Path(LOG_DIR) / LOG_FILE_NAME
def get_logging_status() -> dict[str, Any]:
    root_logger = logging.getLogger()
    return {
        "configured": _LOGGING_CONFIGURED,
        "level": logging.getLevelName(root_logger.level),
        "handlers": [
            {
                "type": type(handler).__name__,
                "level": logging.getLevelName(handler.level),
            }
            for handler in root_logger.handlers
        ],
        "log_file": str(get_log_file_path()),
    }