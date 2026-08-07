"""
Investment recommendation package.
"""

from .engine import RecommendationEngine
from .recommendation import Recommendation
from .signal import Signal

__all__ = [
    "RecommendationEngine",
    "Recommendation",
    "Signal",
]