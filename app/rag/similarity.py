"""
Similarity functions.
"""

from __future__ import annotations

import math


class CosineSimilarity:

    @staticmethod
    def compute(
        a: list[float],
        b: list[float],
    ) -> float:

        if len(a) != len(b):
            raise ValueError("Vector dimensions must match.")

        dot = sum(x * y for x, y in zip(a, b))

        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)