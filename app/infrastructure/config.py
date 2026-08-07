"""
Application configuration.
"""

from __future__ import annotations

import os

from dataclasses import dataclass


@dataclass(slots=True)
class Settings:

    app_name: str = os.getenv(
        "APP_NAME",
        "AI Financial Analyst",
    )

    debug: bool = (
        os.getenv(
            "DEBUG",
            "false",
        ).lower()
        == "true"
    )

    host: str = os.getenv(
        "HOST",
        "0.0.0.0",
    )

    port: int = int(
        os.getenv(
            "PORT",
            "8000",
        )
    )

    environment: str = os.getenv(
        "ENVIRONMENT",
        "development",
    )