"""
Application Logging Configuration

This module configures Python's built-in ``logging`` module with two
output channels:

    1. **Console** — Colored, human-friendly output via ``rich.logging.RichHandler``.
    2. **File** — Machine-parseable, rotating log files via
       ``logging.handlers.RotatingFileHandler``.

Design Decisions:
    - **Rich for console output**: ``RichHandler`` provides colored log levels,
      timestamps, and optional traceback rendering without third-party
      logging frameworks (e.g., ``loguru``). It integrates with any
      ``logging.Logger`` and degrades gracefully in non-TTY environments.
    - **RotatingFileHandler for persistence**: Prevents unbounded log growth
      by capping file size (``LOG_MAX_BYTES``) and retaining a fixed number
      of backups (``LOG_BACKUP_COUNT``).
    - **Idempotent setup**: ``setup_logging()`` clears existing handlers on
      the root logger before adding new ones, preventing duplicate log lines
      when called multiple times (common in tests or FastAPI reloads).
    - **Module-level ``get_logger()``**: A thin wrapper around
      ``logging.getLogger()`` that ensures logging is configured before
      returning a logger, so modules can simply call ``get_logger(__name__)``.
    - **Separation of concerns**: This module only configures handlers and
      formatters. What to log and at what level is decided by the calling
      code.

Usage:
    >>> from app.core.logging import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Application started")
    >>> logger.error("Failed to parse filing", exc_info=True)
"""

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

# ──────────────────────────────────────────────────────────────────────────────
# Module-level flag to track initialization state
# ──────────────────────────────────────────────────────────────────────────────

_LOGGING_CONFIGURED: bool = False


def setup_logging(
    settings: Settings | None = None,
    *,
    force: bool = False,
) -> None:
    """
    Configure the root logger with console and file handlers.

    This function is idempotent: calling it multiple times without
    ``force=True`` is a no-op after the first call. Use ``force=True`` to
    reconfigure logging (e.g., after changing settings in tests).

    Args:
        settings: Optional ``Settings`` instance. If ``None``, the singleton
            from ``get_settings()`` is used.
        force: If ``True``, reconfigure logging even if already configured.
    """
    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED and not force:
        return

    if settings is None:
        settings = get_settings()

    # Resolve log level from settings
    log_level: int = getattr(logging, settings.log_level.value, logging.INFO)

    # Get the root logger and clear any pre-existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    # ── Console Handler (Rich) ───────────────────────────────────────────
    if settings.log_to_console:
        console_handler = RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=settings.debug,
            show_time=True,
            show_level=True,
            show_path=settings.debug,
        )
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(LOG_CONSOLE_FORMAT, datefmt=LOG_DATE_FORMAT))
        root_logger.addHandler(console_handler)

    # ── File Handler (Rotating) ─────────────────────────────────────────
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
        file_handler.setFormatter(
            logging.Formatter(LOG_FILE_FORMAT, datefmt=LOG_DATE_FORMAT)
        )
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    _configure_third_party_loggers(log_level)

    _LOGGING_CONFIGURED = True

    root_logger.debug(
        "Logging configured: level=%s, console=%s, file=%s",
        settings.log_level.value,
        settings.log_to_console,
        settings.log_to_file,
    )


def _configure_third_party_loggers(level: int) -> None:
    """
    Set log levels for noisy third-party libraries.

    Args:
        level: The log level to apply to third-party loggers.
    """
    # These libraries are verbose at INFO; cap them at WARNING in production
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
    """
    Return a configured logger for the given module name.

    This is the primary entry point for all modules that need logging.
    It ensures logging is set up before returning the logger.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A ``logging.Logger`` instance configured with console and/or file
        handlers.
    """
    if not _LOGGING_CONFIGURED:
        setup_logging()
    return logging.getLogger(name)


def shutdown_logging() -> None:
    """
    Flush and close all logging handlers.

    Call this at application shutdown (e.g., in a FastAPI ``lifespan``
    handler) to ensure buffered log records are written to disk.
    """
    logging.shutdown()
    global _LOGGING_CONFIGURED
    _LOGGING_CONFIGURED = False


def get_log_file_path() -> Path:
    """
    Return the absolute path to the current log file.

    Returns:
        A ``Path`` to the main application log file.
    """
    return Path(LOG_DIR) / LOG_FILE_NAME


def get_logging_status() -> dict[str, Any]:
    """
    Return a dictionary describing the current logging configuration.

    Useful for health-check endpoints or debugging.

    Returns:
        A dictionary with ``configured``, ``level``, ``handlers``, and
        ``log_file`` keys.
    """
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