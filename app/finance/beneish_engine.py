"""
Beneish M-Score engine.
"""

from __future__ import annotations

from app.finance.beneish import BeneishMScore


class BeneishEngine:

    def calculate(
        self,
        *,
        dsri: float,
        gmi: float,
        aqi: float,
        sgi: float,
        depi: float,
        sgai: float,
        lvgi: float,
        tata: float,
    ) -> BeneishMScore:

        score = (
            -4.84
            + 0.92 * dsri
            + 0.528 * gmi
            + 0.404 * aqi
            + 0.892 * sgi
            + 0.115 * depi
            - 0.172 * sgai
            + 4.679 * tata
            - 0.327 * lvgi
        )

        return BeneishMScore(score=score)