"""
Workflow pipeline.
"""

from __future__ import annotations

from app.workflow.graph import WorkflowGraph
from app.workflow.node import WorkflowNode


class WorkflowPipeline:

    def build(self) -> WorkflowGraph:

        graph = WorkflowGraph()

        graph.add_node(
            WorkflowNode("planner"),
        )

        graph.add_node(
            WorkflowNode("retriever"),
        )

        graph.add_node(
            WorkflowNode("quant"),
        )

        graph.add_node(
            WorkflowNode("writer"),
        )

        graph.add_node(
            WorkflowNode("auditor"),
        )

        return graph