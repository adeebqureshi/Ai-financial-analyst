"""
code_agent.py

FinancialCodeAgent — turns a natural-language calculation request into code
that runs *inside the sandbox* and returns the sandbox-computed numeric result.

The trusted result never comes straight from the LLM. The LLM only writes the
formula/code; the arithmetic is performed by :class:`PythonSandbox`. The final
answer must be assigned to ``result`` inside the generated code.

Input-data discipline
---------------------
The sandbox receives **only** the explicitly supplied ``context`` (real values
from the application's financial-data tools). The code agent's prompt forbids
the LLM from inventing inputs, and the sandbox structurally enforces this:
any variable name that was not supplied raises a ``NameError`` at runtime. The
sandbox verifies arithmetic; it does **not** verify the truth of the input
data — that is the application's data layer's responsibility.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.llm.exceptions import LLMError
from app.llm.models import LLMRequest
from app.llm.openai_client import OpenAIClient
from app.sandbox.executor import PythonSandbox, SandboxResult

logger = get_logger(__name__)

_CODE_FENCE_PATTERN = re.compile(
    r"```(?:python|py)?\s*\n(.*?)```",
    re.DOTALL,
)


@dataclass(slots=True)
class CodeAgentResult:
    """
    Result of the code generation → sandbox execution pipeline.

    Attributes:
        success: ``True`` when the generated code validated, executed and
            produced a ``result`` inside the sandbox.
        code: The exact code that ran in the sandbox.
        output: Captured stdout from the sandbox execution.
        result: The sandbox-computed ``result`` value.
        error: Structured error when ``success`` is ``False``.
    """

    success: bool
    code: str = ""
    output: str = ""
    result: Any | None = None
    error: str | None = None


class FinancialCodeAgent:
    """
    Generate a formula from a request and execute it in the sandbox.

    The LLM is the *code writer*; the sandbox is the *calculator*. The numeric
    answer returned by :meth:`run` is the sandbox's ``result``, never a number
    the LLM printed.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        llm_client: OpenAIClient | None = None,
        sandbox: PythonSandbox | None = None,
    ) -> None:
        settings = settings or get_settings()

        self._client = llm_client or OpenAIClient()
        self._sandbox = sandbox or PythonSandbox(timeout=settings.sandbox_timeout)

    def run(
        self,
        question: str,
        context: dict[str, Any] | None = None,
    ) -> CodeAgentResult:
        """
        Generate and sandbox-execute Python for ``question``.

        Args:
            question: The calculation request (e.g. "What is Apple's WACC?").
            context: Real financial values supplied by the application's
                data tools. Only these values are visible to the code.

        Returns:
            A :class:`CodeAgentResult`; ``success`` is ``True`` only when the
            sandbox produced a result.
        """
        prompt = _build_calculation_prompt(question, context)

        try:
            response = self._client.generate(LLMRequest(prompt=prompt))
        except LLMError as exc:
            logger.warning("Calculation LLM call failed: %s", exc)
            return CodeAgentResult(
                success=False,
                error=f"LLM error: {exc}",
            )

        code = _extract_code(response.text)

        if code is None:
            return CodeAgentResult(
                success=False,
                error="LLM response contained no valid Python code.",
            )

        sandbox_result = self._sandbox.run(code, context=context)

        return _to_agent_result(sandbox_result, code)


def _to_agent_result(
    sandbox_result: SandboxResult,
    code: str,
) -> CodeAgentResult:
    if not sandbox_result.success:
        return CodeAgentResult(
            success=False,
            code=code,
            output=sandbox_result.output,
            error=sandbox_result.error,
        )

    if sandbox_result.return_value is None:
        return CodeAgentResult(
            success=False,
            code=code,
            output=sandbox_result.output,
            error="the generated code produced no 'result' value",
        )

    return CodeAgentResult(
        success=True,
        code=code,
        output=sandbox_result.output,
        result=sandbox_result.return_value,
    )


def _extract_code(text: str) -> str | None:
    """
    Extract Python source from an LLM response.

    Prefers the longest fenced code block (```python ... ```). When the
    response has no fence, falls back to the whole (stripped) text only if it
    parses as valid Python — so explanatory prose is never executed.
    """
    if not text:
        return None

    fenced: list[str] = _CODE_FENCE_PATTERN.findall(text)
    if fenced:
        candidate = max(fenced, key=len).strip()
        if _is_valid_python(candidate):
            return candidate

    stripped = text.strip()
    if _is_valid_python(stripped):
        return stripped

    return None


def _is_valid_python(source: str) -> bool:
    try:
        ast.parse(source, mode="exec")
    except SyntaxError:
        return False
    return True


def _build_calculation_prompt(
    question: str,
    context: dict[str, Any] | None,
) -> str:
    context_block = json.dumps(context or {}, indent=2, default=_json_default)

    variables = ", ".join(name for name in (context or {}) if isinstance(name, str)) or "none"

    return f"""You write a small Python script that computes a financial formula.
A real data layer already produced the input values. You MUST use ONLY the
provided variables — never invent, approximate or hardcode any number.

RULES:
- Only the following variables exist. Do NOT define new ones:
  {variables}
- Every number in your code MUST come from these variables or from constants
  you compute from them (e.g. a model's tax rate). Inventing financial inputs
  is forbidden and will fail: referencing an undefined name raises a runtime
  error.
- Do NOT import anything. Do NOT use files, network, subprocesses or
  os/sys/eval/exec/compile.
- Use only arithmetic and the provided values.
- Assign the final answer to a variable named exactly: result
- If the question cannot be answered from the provided variables, assign
  result = None (and explain in a comment).
- Reply with ONLY a python code block, e.g.:

```python
result = context["revenue"] * 0.4
```

Question: {question}

--- PROVIDED DATA (also available as individual variables) ---
{context_block}
"""


def _json_default(value: Any) -> str:
    return str(value)


__all__ = [
    "CodeAgentResult",
    "FinancialCodeAgent",
    "build_calculation_prompt",
]


def build_calculation_prompt(
    question: str,
    context: dict[str, Any] | None,
) -> str:
    """Public helper (testable) mirroring the internal prompt builder."""
    return _build_calculation_prompt(question, context)
