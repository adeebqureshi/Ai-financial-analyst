"""
Coordinator Agent.
"""

from __future__ import annotations

from app.agents.analysis_result import AnalysisResult
from app.agents.auditor import AuditorAgent
from app.agents.planner import PlannerAgent
from app.agents.quant import QuantAgent
from app.agents.report_writer import ReportWriterAgent
from app.agents.retrieval_result import RetrievalResult
from app.agents.retriever import RetrieverAgent
from app.agents.workflow_result import WorkflowResult
from app.rag.embedding import Embedding


class CoordinatorAgent:
    """
    Coordinates the complete AI financial analysis workflow.
    """

    def __init__(self) -> None:

        self.planner = PlannerAgent()

        self.retriever = RetrieverAgent()

        self.quant = QuantAgent()

        self.writer = ReportWriterAgent()

        self.auditor = AuditorAgent()

    def run(
        self,
        query: str,
        documents: list[Embedding],
    ) -> WorkflowResult:

        self.planner.plan(query)

        retrieval = self.retriever.retrieve(
            query,
            documents,
        )

        analysis = self.quant.analyze(
            company="Unknown Company",
        )

        report = self.writer.write(
            retrieval,
            analysis,
        )

        audit = self.auditor.audit(
            report,
        )

        success = (
            audit
            if isinstance(audit, bool)
            else audit.passed
        )

        return WorkflowResult(
            report=report,
            success=success,
        )