"""Guards against the `app.orchestrator` import cycle.

Previously ``analysis_service`` imported ``FinancialPipeline`` at module level,
closing the loop::

    pipeline -> app.agents -> coordinator -> app.services -> analysis_service
             -> pipeline

which made ``import app.orchestrator.pipeline`` fail whenever it happened to be
the first import. The suite masked this because ``conftest`` imports
``app.main`` first. ``FinancialPipeline`` is now imported lazily inside
``AnalysisService._get_pipeline``.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

_MODULES = [
    "app.orchestrator.pipeline",
    "app.services.analysis_service",
    "app.agents.coordinator",
    "app.agents.tools",
    "app.main",
]


@pytest.mark.parametrize("module", _MODULES)
def test_module_imports_cleanly_in_a_fresh_interpreter(module: str) -> None:
    """Each module must import first, in its own process, with no cycle."""
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert result.returncode == 0, (
        f"importing {module} first failed:\n{result.stderr[-1500:]}"
    )


def test_pipeline_exposes_financial_pipeline() -> None:
    from app.orchestrator.pipeline import FinancialPipeline

    assert hasattr(FinancialPipeline, "analyze_company")
