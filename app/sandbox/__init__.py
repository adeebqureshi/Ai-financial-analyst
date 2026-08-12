"""
Sandboxed financial code execution (Phase 4).

LLM-generated Python is untrusted input. It is validated with an AST-level
security check and executed inside a restricted namespace with a controlled
builtins dictionary, then returns a structured :class:`SandboxResult`.
"""

from __future__ import annotations

from app.sandbox.code_agent import CodeAgentResult, FinancialCodeAgent
from app.sandbox.executor import (
    MAX_CODE_LENGTH,
    PythonSandbox,
    SandboxResult,
    SandboxSecurityError,
)

__all__ = [
    "CodeAgentResult",
    "FinancialCodeAgent",
    "MAX_CODE_LENGTH",
    "PythonSandbox",
    "SandboxResult",
    "SandboxSecurityError",
]
