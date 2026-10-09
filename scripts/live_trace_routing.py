"""Live end-to-end routing trace against the indexed apple 10k.pdf.

Exercises the real path for both quick actions:
  PlannerAgent -> ToolRegistry.execute("search_documents")
  -> DocumentService.retrieve -> RetrievalEngine -> Qdrant -> chunks
and reports the evidence that would be handed to the analyst.

Usage: .venv/Scripts/python.exe scripts/live_trace_routing.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.planner import PlannerAgent
from app.agents.tools import ToolRegistry
from app.core.config import get_settings
from app.services.document_service import DocumentService

QUERIES = [
    "Summarize key risks",
    "Compare margins by segment",
    "What are Apple's major risks?",
    "What risks are mentioned in this 10-K?",
    "What are the major supply-chain risks?",
]


def main() -> None:
    registry = ToolRegistry(documents=DocumentService(get_settings()))
    for query in QUERIES:
        plan = PlannerAgent().plan(query)
        print("=" * 78)
        print(f"QUERY: {query!r}")
        print(f"  intents      : {[i.value for i in plan.intents]}")
        print(f"  tickers      : {plan.tickers}")
        print(f"  needs_rag    : {plan.needs_rag}")
        print(f"  planned tools: {plan.tool_names}")
        usable = 0
        for call in plan.tools:
            if call.tool != "search_documents":
                continue
            print(f"  search_documents args: {call.args}")
            result = registry.execute("search_documents", call.args, owner_id="anonymous")
            print(f"  status: {result.status}  error: {result.error}")
            if result.status != "done" or not result.result:
                continue
            chunks = result.result.get("chunks", [])
            usable += len(chunks)
            print(f"  RETRIEVED CHUNKS: {len(chunks)}")
            for chunk in chunks:
                head = " ".join(chunk["text"].split())[:110]
                print(
                    f"    p.{chunk['page']:<4} score={chunk['score']:.3f} "
                    f"[{chunk.get('section') or '-'}] {head}"
                )
        print(f"  evidence chunks handed to analyst: {usable}")
        if usable == 0:
            print("  >> EMPTY EVIDENCE -> analyst would return fallback")
    print("=" * 78)


if __name__ == "__main__":
    main()