"""
Request ID utilities.
"""

from __future__ import annotations

import uuid


def generate_request_id() -> str:
    return str(uuid.uuid4())