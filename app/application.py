from __future__ import annotations

from app.api.app import FinancialAnalystAPI


class Application:

    def __init__(self) -> None:
        self.api = FinancialAnalystAPI()

    def analyze(
        self,
        ticker: str,
        query: str,
        result: dict,
        context: str,
    ):
        return self.api.analyze(
            ticker=ticker,
            query=query,
            result=result,
            context=context,
        )