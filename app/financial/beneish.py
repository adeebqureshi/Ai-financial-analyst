"""
beneish.py

Beneish M-Score model.
"""

from __future__ import annotations


class BeneishMScore:

    @staticmethod
    def calculate(
        dsri: float,
        gmi: float,
        aqi: float,
        sgi: float,
        depi: float,
        sgai: float,
        lvgi: float,
        tata: float,
    ) -> float:

        return (
            -4.84
            + 0.920 * dsri
            + 0.528 * gmi
            + 0.404 * aqi
            + 0.892 * sgi
            + 0.115 * depi
            - 0.172 * sgai
            + 4.679 * tata
            - 0.327 * lvgi
        )

    @staticmethod
    def interpretation(
        score: float,
    ) -> str:

        if score > -1.78:
            return "HIGH_RISK"

        return "LOW_RISK"