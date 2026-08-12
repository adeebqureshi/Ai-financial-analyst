"""
Security and behaviour tests for the restricted sandbox (app.sandbox.executor).

The sandbox runs LLM-generated (untrusted) Python. These tests verify it
only arithmetic + supplied data; it never leaks the host process.
"""

import signal

import pytest

from app.sandbox.executor import PythonSandbox, SandboxResult


@pytest.fixture(scope="module")
def sandbox() -> PythonSandbox:
    return PythonSandbox()


# ──────────────────────────────────────────────────────────────────────
# Happy path
# ──────────────────────────────────────────────────────────────────────


def test_basic_arithmetic(sandbox):
    result = sandbox.run("result = 2 + 2")

    assert result.success
    assert result.return_value == 4
    assert result.error is None


def test_financial_formula_with_supplied_context(sandbox):
    context = {
        "equity": 800.0,
        "debt": 200.0,
        "cost_of_equity": 0.10,
        "cost_of_debt": 0.05,
        "tax_rate": 0.21,
    }
    code = (
        "total = equity + debt\n"
        "wacc = (equity / total) * cost_of_equity + "
        "(debt / total) * cost_of_debt * (1 - tax_rate)\n"
        "result = wacc"
    )

    result = sandbox.run(code, context=context)

    assert result.success
    expected = (800 / 1000) * 0.10 + (200 / 1000) * 0.05 * (1 - 0.21)
    assert result.return_value == pytest.approx(expected)


def test_context_accessible_via_dict_and_flattened_names(sandbox):
    code = "a = context['revenue']\nb = revenue\nresult = a + b"

    result = sandbox.run(code, context={"revenue": 1_000.0})

    assert result.success
    assert result.return_value == 2_000.0


def test_invented_variable_fails_at_runtime(sandbox):
    """A name that was never supplied must raise NameError, not be invented."""
    result = sandbox.run("result = mr_apple_rev * 2")

    assert not result.success
    assert "NameError" in result.error


def test_math_helpers_available(sandbox):
    result = sandbox.run("result = sqrt(2)")

    assert result.success
    assert result.return_value == pytest.approx(1.41421, abs=1e-4)


def test_result_extraction(sandbox):
    result = sandbox.run("x = 6\nresult = x * 7")

    assert result.success
    assert result.return_value == 42


def test_output_capture(sandbox):
    result = sandbox.run('print("start")\nprint(123)\nresult = 1')

    assert result.success
    assert result.output == "start\n123\n"
    assert result.return_value == 1


def test_control_flow_loops_and_comprehensions_allowed(sandbox):
    code = (
        "total = 0\n"
        "for i in range(5):\n"
        "    total += i\n"
        "squares = [x * x for x in range(3)]\n"
        "result = total + len(squares)"
    )

    result = sandbox.run(code)

    assert result.success
    assert result.return_value == 10 + 3


# ──────────────────────────────────────────────────────────────────────
# Structured failures
# ──────────────────────────────────────────────────────────────────────


def test_runtime_error_is_structured(sandbox):
    result = sandbox.run("result = 1 / 0")

    assert isinstance(result, SandboxResult)
    assert not result.success
    assert result.return_value is None
    assert "ZeroDivisionError" in result.error


def test_syntax_error_is_structured(sandbox):
    result = sandbox.run("result = (")

    assert not result.success
    assert "syntax error" in result.error.lower()


def test_empty_code_rejected(sandbox):
    result = sandbox.run("   ")

    assert not result.success
    assert "security" in result.error


def test_explicit_none_result_is_success(sandbox):
    result = sandbox.run("result = None")

    assert result.success
    assert result.return_value is None


def test_print_after_error_still_captured(sandbox):
    result = sandbox.run('print("before")\nresult = 1 / 0')

    assert not result.success
    assert result.output == "before\n"


# ──────────────────────────────────────────────────────────────────────
# Forbidden operations
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "code",
    [
        "import os",
        "from os import system",
        "import sys",
        "import subprocess",
        "from subprocess import check_output",
        "import socket",
        "import urllib.request",
        "import requests",
        "import pathlib",
        "import builtins",
        "result = open('x')",
        "result = open('/etc/passwd')",
        "result = eval('1 + 1')",
        "result = exec('print(1)')",
        "result = compile('print(1)', '<x>', 'exec')",
        "result = __import__('os')",
        "result = globals()",
        "result = locals()",
        "result = vars()",
        "result = dir()",
        "result = __builtins__['eval']",
        "result = getattr(Dict, '__class__')",
        "result = setattr(Dict, 'x', 1)",
        "result = os.system('calc')",
        "result = sys.modules",
        "result = subprocess.call(['ls'])",
        "result = (1).__class__",
        "result = str.__mro__",
        "result = ''.__class__.__base__.__subclasses__()",
        "result = [].__class__.__base__.__subclasses__()",
        "result = {}.__class__",
        "f = lambda: 1\nresult = f.__globals__",
        "result = int.__subclasses__()",
        "class Esc:\n    pass\nresult = Esc",
        "global x\nresult = 1",
        "async def f():\n    return 1\nresult = 1",
        "result = input('prompt')",
    ],
)
def test_forbidden_operations_rejected(sandbox, code):
    result = sandbox.run(code)

    assert not result.success
    assert result.error.startswith("security:")


@pytest.mark.parametrize(
    "code",
    [
        "result = os.system('echo hi')",
        "result = __import__('socket')",
        'result = "x".__init__.__getattribute__("__class__")',
    ],
)
def test_ast_level_bypass_attempts_rejected(sandbox, code):
    result = sandbox.run(code)

    assert not result.success


def test_double_underscore_attribute_blocked(sandbox):
    result = sandbox.run("result = 'x'.__class__")

    assert not result.success
    assert "dunder attribute" in result.error


def test_context_only_contains_supplied_data(sandbox):
    """The namespace contains exactly the supplied values — nothing more."""
    result = sandbox.run(
        "result = sorted(context.keys())",
        context={"equity": 1.0, "risk_free_rate": 0.04},
    )

    assert result.success
    assert result.return_value == ["equity", "risk_free_rate"]


def test_host_builtins_not_mutated(sandbox):
    before = dir(SandboxResult)
    sandbox.run("result = 2")
    after = dir(SandboxResult)

    assert before == after


# ──────────────────────────────────────────────────────────────────────
# Timeout (POSIX-only; skipped on Windows)
# ──────────────────────────────────────────────────────────────────────


def test_timeout_enforced_when_sigalrm_available(sandbox):
    if not hasattr(signal, "SIGALRM"):
        pytest.skip("SIGALRM not available on this platform")

    result = sandbox.run("while True:\n    pass", timeout=1)

    assert not result.success
    assert "timeout" in result.error.lower()


def test_validate_reports_reason():
    sandbox = PythonSandbox()

    assert sandbox.validate("import os") is not None
    assert sandbox.validate("result = 1 + 1") is None
