"""
Tests for FinancialCodeAgent — the LLM → sandbox → result pipeline.

The LLM is a *code writer*; the trusted numeric result always comes from
sandbox execution.
"""

from types import SimpleNamespace

import pytest

from app.llm.exceptions import LLMError
from app.sandbox.code_agent import CodeAgentResult, FinancialCodeAgent, _extract_code
from app.sandbox.executor import PythonSandbox


def _llm(text):
    return SimpleNamespace(generate=lambda request: SimpleNamespace(text=text))


def _agent(llm) -> FinancialCodeAgent:
    return FinancialCodeAgent(
        llm_client=llm,
        sandbox=PythonSandbox(),
    )


def test_llm_code_executed_through_sandbox_with_context():
    llm = _llm("```python\nresult = context['revenue'] * 0.4\n```")
    agent = _agent(llm)

    outcome = agent.run(
        question="What is 40% of revenue?",
        context={"revenue": 1_000.0},
    )

    assert isinstance(outcome, CodeAgentResult)
    assert outcome.success
    assert outcome.result == 400.0
    assert outcome.code == "result = context['revenue'] * 0.4"
    assert outcome.error is None


def test_llm_code_can_flatten_provided_variables():
    llm = _llm(
        "```python\ncost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)\n"
        "result = cost_of_equity\n```"
    )
    agent = _agent(llm)

    outcome = agent.run(
        question="Cost of equity?",
        context={"risk_free_rate": 0.04, "beta": 1.2, "market_return": 0.10},
    )

    assert outcome.success
    assert outcome.result == pytest.approx(0.04 + 1.2 * 0.06)


def test_output_captured_through_pipeline():
    llm = _llm("```python\nprint('computed')\nresult = 7\n```")
    agent = _agent(llm)

    outcome = agent.run(question="Simple", context={})

    assert outcome.success
    assert outcome.output == "computed\n"
    assert outcome.result == 7


def test_no_code_in_response_is_controlled_failure():
    agent = _agent(_llm("I cannot write code for this request."))

    outcome = agent.run(question="What?", context={})

    assert not outcome.success
    assert "no valid Python code" in outcome.error


def test_markdown_prose_without_fence_rejected():
    """Explanatory prose is never executed."""
    agent = _agent(_llm("Here is some prose that is not valid python code talk"))

    outcome = agent.run(question="?", context={})

    assert not outcome.success


def test_sandbox_runtime_error_mapped_into_result():
    agent = _agent(_llm("```python\nresult = 1 / 0\n```"))

    outcome = agent.run(question="?", context={})

    assert not outcome.success
    assert "ZeroDivisionError" in outcome.error
    assert outcome.code


def test_llm_invented_variable_fails():
    """The LLM cannot fabricate inputs: undefined names raise NameError."""
    agent = _agent(_llm("```python\nresult = invented_eps * 10\n```"))

    outcome = agent.run(question="EPS?", context={})

    assert not outcome.success
    assert "NameError" in outcome.error


def test_no_result_assignment_is_failure():
    agent = _agent(_llm("```python\nprint('no result here')\n```"))

    outcome = agent.run(question="?", context={})

    assert not outcome.success
    assert "no 'result' value" in outcome.error


def test_llm_error_is_structured_failure():
    class BrokenLLM:
        def generate(self, request):
            raise LLMError("provider down")

    outcome = _agent(BrokenLLM()).run(question="?", context={})

    assert not outcome.success
    assert "LLM error" in outcome.error


def test_insecure_code_rejected_before_execution():
    agent = _agent(_llm("```python\nimport os\nresult = os.system('calc')\n```"))

    outcome = agent.run(question="?", context={})

    assert not outcome.success
    assert "security" in outcome.error


def test_question_included_in_prompt():
    captured = {}

    class RecordingLLM:
        def generate(self, request):
            captured["prompt"] = request.prompt
            return SimpleNamespace(text="```python\nresult = 1\n```")

    agent = _agent(RecordingLLM())
    agent.run(question="WACC for Apple", context={"beta": 1.2})

    assert "WACC for Apple" in captured["prompt"]
    assert "result" in captured["prompt"]
    assert "1.2" in captured["prompt"]


# ──────────────────────────────────────────────────────────────────────
# Code extraction
# ──────────────────────────────────────────────────────────────────────


def test_extract_code_prefers_fenced_block():
    text = "Here is the code:\n```python\nresult = 2 + 2\n```\nDone."

    assert _extract_code(text) == "result = 2 + 2"


def test_extract_picks_longest_fence():
    text = "```python\nresult = 1\n```\n```python\nresult = 10 + 5\n```"

    assert _extract_code(text) == "result = 10 + 5"


def test_extract_plain_valid_python_fallback():
    assert _extract_code("result = 3 * 3") == "result = 3 * 3"


def test_extract_plain_invalid_python_returns_none():
    assert _extract_code("result = (") is None
    assert _extract_code("def broken(:") is None


def test_extract_empty_returns_none():
    assert _extract_code("") is None


def test_extract_fence_without_language():
    text = "```\nresult = 1\n```"

    assert _extract_code(text) == "result = 1"
