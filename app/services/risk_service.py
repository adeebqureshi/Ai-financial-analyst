from __future__ import annotations
from app.core.config import Settings
from app.financial.altman import AltmanZScore
from app.financial.beneish import BeneishMScore
from app.financial.health import FinancialHealth
from app.schemas.analysis import RiskAnalysisRequest
from app.schemas.responses import RiskAssessmentData
class RiskService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
    def assess(self, request: RiskAnalysisRequest) -> RiskAssessmentData:
        health_score = FinancialHealth.score(
            request.piotroski_score,
            request.altman_score,
            request.beneish_score,
        )
        health_rating = FinancialHealth.rating(health_score)
        altman_int = AltmanZScore.interpretation(request.altman_score)
        beneish_int = BeneishMScore.interpretation(request.beneish_score)
        if health_score >= 85 and altman_int == "SAFE" and beneish_int == "LOW_RISK":
            risk_level = "LOW"
        elif health_score >= 50:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        return RiskAssessmentData(
            health_score=health_score,
            health_rating=health_rating,
            piotroski={"score": request.piotroski_score, "max": 9},
            altman={"score": request.altman_score, "interpretation": altman_int},
            beneish={"score": request.beneish_score, "interpretation": beneish_int},
            risk_level=risk_level,
        )