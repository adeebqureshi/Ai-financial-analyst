"""
processing_status.py

Processing status used throughout the AI Financial Analyst pipeline.
"""

from enum import Enum


class ProcessingStatus(str, Enum):
    """
    Represents the processing state of a pipeline stage.
    """

    PENDING = "pending"

    IN_PROGRESS = "in_progress"

    COMPLETED = "completed"

    FAILED = "failed"

    SKIPPED = "skipped"