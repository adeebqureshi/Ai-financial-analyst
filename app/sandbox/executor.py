"""
executor.py

Restricted Python execution environment for LLM-generated financial code.

Threat model
------------
Code produced by an LLM is treated as **untrusted input**. The sandbox is a
defence-in-depth layer: an AST-level validation pass runs first and rejects
dangerous constructs before any execution; the runtime then provides a
controlled namespace with a restricted ``builtins`` dictionary and no modules.

Guarantees provided here (in-process):
    - No arbitrary imports (``import`` / ``from`` statements are rejected).
    - No ``exec`` / ``eval`` / ``compile`` / ``__import__``.
    - No ``open`` or filesystem access.
    - No ``subprocess`` / system calls (no ``sys``, ``os``, ``subprocess``).
    - No network clients (no ``socket``, ``urllib``, ``http``, ``requests``).
    - No ``__builtins__``, object/class hierarchy or ``globals()`` escape
      (dunder attribute access is rejected, as are ``globals``/``locals``).
    - stdout is captured; exceptions are converted into a structured
      :class:`SandboxResult`; the final answer is read from ``result``.

Limitations (documented, not hidden)
------------------------------------
This is a **restricted in-process ``exec()`` sandbox**, *not* an OS-level
process/container sandbox. It is intended to stop accidental or opportunistic
escapes by generated code, not a determined local attacker who already has
Python interpreter access on the host.

    - Timeout enforcement uses ``SIGALRM`` where the platform provides it
      (POSIX, main thread). On Windows there is no ``SIGALRM``, so an
      infinite loop cannot be interrupted from within the process; a
      production deployment that executes untrusted code must run it in a
      separate process/container with a hard kill timer and memory limits.
    - Memory limits require OS-level controls (e.g. ``resource.setrlimit`` /
      container ``--memory``) and are not applied here.
    - The sandbox verifies **arithmetic** — it does not verify whether the
      input financial data is true. Real data must be supplied by the
      application's financial-data tools (see ``app.sandbox.code_agent``).
"""

from __future__ import annotations

import ast
import builtins
import contextlib
import io
import math
import signal
import threading
from dataclasses import dataclass
from typing import Any, Final

from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_CODE_LENGTH: Final[int] = 8000
"""Maximum number of characters of sandboxed code. Static cost guard."""

SANDBOX_SOURCE_NAME: Final[str] = "<sandbox>"


class SandboxSecurityError(Exception):
    """Raised when sandboxed code attempts a blocked operation."""


class SandboxTimeoutError(TimeoutError):
    """Raised when sandboxed execution exceeds the configured time budget."""


# ─────────────────────────────────────────────────────────────────────────────
# Controlled builtins
# ─────────────────────────────────────────────────────────────────────────────

# Pure, side-effect-free builtins every financial formula may rely on.
_BASIC_BUILTIN_NAMES: Final[tuple[str, ...]] = (
    "abs",
    "all",
    "any",
    "bin",
    "bool",
    "chr",
    "complex",
    "dict",
    "divmod",
    "enumerate",
    "filter",
    "float",
    "format",
    "frozenset",
    "hash",
    "hex",
    "int",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "list",
    "map",
    "max",
    "min",
    "next",
    "oct",
    "ord",
    "pow",
    "print",
    "range",
    "repr",
    "reversed",
    "round",
    "set",
    "slice",
    "sorted",
    "str",
    "sum",
    "tuple",
    "type",
    "zip",
)

# Exception types so ``try/except`` clauses resolve inside the sandbox.
_EXCEPTION_NAMES: Final[tuple[str, ...]] = (
    "ArithmeticError",
    "AssertionError",
    "BaseException",
    "Exception",
    "IndexError",
    "KeyError",
    "LookupError",
    "MemoryError",
    "NameError",
    "OverflowError",
    "RuntimeError",
    "StopIteration",
    "TypeError",
    "ValueError",
    "ZeroDivisionError",
)

# Math helpers commonly needed by DCF / WACC / ratio formulas.
_MATH_FUNCTION_NAMES: Final[tuple[str, ...]] = (
    "ceil",
    "comb",
    "copysign",
    "exp",
    "fabs",
    "floor",
    "fsum",
    "gcd",
    "hypot",
    "isfinite",
    "isinf",
    "isnan",
    "log",
    "log10",
    "log2",
    "perm",
    "prod",
    "sqrt",
    "trunc",
)

_MATH_CONSTANTS: Final[dict[str, float]] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def _build_safe_builtins() -> dict[str, Any]:
    """Build the controlled ``builtins`` dictionary exposed to sandboxed code."""
    safe: dict[str, Any] = {}

    for name in _BASIC_BUILTIN_NAMES + _EXCEPTION_NAMES:
        safe[name] = getattr(builtins, name)

    for name in _MATH_FUNCTION_NAMES:
        safe[name] = getattr(math, name)

    safe.update(_MATH_CONSTANTS)

    return safe


SAFE_BUILTINS: Final[dict[str, Any]] = _build_safe_builtins()

# Names that are never available to sandboxed code — neither as plain names
# nor as attributes. Accessing any of them (read, write or delete) is
# rejected at the AST level.
_FORBIDDEN_NAMES: Final[frozenset[str]] = frozenset(
    {
        # modules
        "os",
        "sys",
        "subprocess",
        "socket",
        "urllib",
        "http",
        "requests",
        "pathlib",
        "shutil",
        "pickle",
        "marshal",
        "shelve",
        "ctypes",
        "multiprocessing",
        "threading",
        "asyncio",
        "resource",
        "builtins",
        "importlib",
        "base64",
        "codecs",
        "telnetlib",
        "ftplib",
        "smtplib",
        "poplib",
        "imaplib",
        "ssl",
        "glob",
        "tempfile",
        "io",
        # dynamic execution / introspection
        "eval",
        "exec",
        "compile",
        "__import__",
        "globals",
        "locals",
        "vars",
        "dir",
        "input",
        "breakpoint",
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
        "memoryview",
        "id",
        # filesystem
        "open",
        "file",
        # interpreter exits
        "exit",
        "quit",
        "help",
        "copyright",
        "credits",
        "license",
        # dunder module/namespace names
        "__builtins__",
        "__loader__",
        "__spec__",
        "__package__",
        "__name__",
        "__file__",
        "__cached__",
        "__doc__",
        "__annotations__",
    }
)


# ─────────────────────────────────────────────────────────────────────────────
# AST-level security validation
# ─────────────────────────────────────────────────────────────────────────────


class SandboxValidator:
    """
    AST-level static check that rejects dangerous Python constructs.

    Validation happens *before* any execution, so a rejected program never
    starts running. The checks are structural (they inspect the parsed tree)
    rather than string matches, which defeats simple textual obfuscation,
    while still allowing legitimate arithmetic.
    """

    def validate(self, code: str) -> str | None:
        """
        Return ``None`` when ``code`` is safe, otherwise a human-readable
        reason why it was rejected.
        """
        if not code.strip():
            return "empty code"

        if len(code) > MAX_CODE_LENGTH:
            return f"code exceeds the maximum length of {MAX_CODE_LENGTH} characters"

        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError as exc:
            location = f" (line {exc.lineno})" if exc.lineno else ""
            return f"syntax error: {exc.msg}{location}"

        for node in ast.walk(tree):
            reason = self._check_node(node)
            if reason:
                return reason

        return None

    def _check_node(self, node: ast.AST) -> str | None:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return "imports are not allowed in sandboxed code"

        if isinstance(node, ast.ClassDef):
            return "class definitions are not allowed in sandboxed code"

        if isinstance(node, (ast.AsyncFunctionDef, ast.Await, ast.Yield, ast.YieldFrom)):
            return "async/yield constructs are not allowed in sandboxed code"

        if isinstance(node, (ast.Global, ast.Nonlocal)):
            return "global/nonlocal statements are not allowed in sandboxed code"

        if isinstance(node, ast.Attribute):
            attr = node.attr
            if attr.startswith("__"):
                return (
                    f"access to dunder attribute '{attr}' is not allowed "
                    "(namespace escapes are blocked)"
                )
            if attr in _FORBIDDEN_NAMES:
                return f"access to '{attr}' is not allowed in sandboxed code"

        if isinstance(node, ast.Name):
            if node.id in _FORBIDDEN_NAMES:
                return f"use of '{node.id}' is not allowed in sandboxed code"

        return None


# ─────────────────────────────────────────────────────────────────────────────
# Structured result
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(slots=True)
class SandboxResult:
    """
    Structured outcome of one sandboxed execution.

    Attributes:
        success: ``True`` when the code validated and executed without error;
            ``False`` on validation rejection, syntax error, runtime error or
            timeout.
        output: Captured stdout produced by ``print()`` calls.
        error: ``None`` on success; otherwise a short, structured error
            message (never a raw traceback).
        return_value: The value of ``result`` at the end of execution, or
            ``None`` when the code did not define it.
    """

    success: bool
    output: str
    error: str | None = None
    return_value: Any | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Executor
# ─────────────────────────────────────────────────────────────────────────────


class PythonSandbox:
    """
    Restricted in-process Python execution environment.

    The sandbox never receives the application's environment, secrets,
    database connections or filesystem; it only sees the explicitly supplied
    ``context`` values and the controlled builtins.

    Args:
        timeout: Optional wall-clock budget in seconds. Enforced with
            ``SIGALRM`` where the platform supports it; on Windows (no
            ``SIGALRM``) the budget is informational. See the module docstring
            for the documented limitation.
    """

    def __init__(self, timeout: int | None = None) -> None:
        self.timeout = timeout

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def validate(self, code: str) -> str | None:
        """Return ``None`` if ``code`` passes validation, else the reason."""
        return SandboxValidator().validate(code)

    def run(
        self,
        code: str,
        context: dict[str, Any] | None = None,
        *,
        timeout: int | None = None,
    ) -> SandboxResult:
        """
        Validate and execute ``code`` inside the restricted namespace.

        Args:
            code: The untrusted Python source to run.
            context: Explicit values the code may reference. Every value is
                injected into the namespace under its key; no other data is
                visible to the code.
            timeout: Optional override for the configured timeout.

        Returns:
            A structured :class:`SandboxResult`. Exceptions never propagate.
        """
        namespace = self._build_namespace(context)

        reason = self.validate(code)
        if reason:
            return SandboxResult(
                success=False,
                output="",
                error=f"security: {reason}",
            )

        try:
            compiled = compile(code, SANDBOX_SOURCE_NAME, "exec")
        except SyntaxError as exc:
            return SandboxResult(
                success=False,
                output="",
                error=f"syntax error: {exc.msg}",
            )

        output, error = self._execute(compiled, namespace, timeout)

        if error is not None:
            return SandboxResult(
                success=False,
                output=output,
                error=error,
            )

        return SandboxResult(
            success=True,
            output=output,
            return_value=namespace.get("result"),
        )

    # ──────────────────────────────────────────────────────────────────────
    # Internals
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_namespace(context: dict[str, Any] | None) -> dict[str, Any]:
        supplied = dict(context or {})

        namespace: dict[str, Any] = {
            "__builtins__": SAFE_BUILTINS,
            "context": supplied,
        }

        for key, value in supplied.items():
            if (
                isinstance(key, str)
                and key.isidentifier()
                and key not in _FORBIDDEN_NAMES
                and key != "context"
                and key != "result"
            ):
                namespace[key] = value

        return namespace

    def _execute(
        self,
        compiled: Any,
        namespace: dict[str, Any],
        timeout: int | None,
    ) -> tuple[str, str | None]:
        effective_timeout = timeout if timeout is not None and timeout > 0 else None
        effective_timeout = effective_timeout or self.timeout

        buffer = io.StringIO()

        try:
            with contextlib.redirect_stdout(buffer):
                if (
                    effective_timeout is not None
                    and hasattr(signal, "SIGALRM")
                    and threading.current_thread() is threading.main_thread()
                ):
                    self._exec_with_timeout(compiled, namespace, effective_timeout)
                else:
                    if effective_timeout is not None:
                        logger.debug(
                            "Sandbox timeout requested but SIGALRM is unavailable "
                            "on this platform/thread; running without a hard timeout."
                        )
                    exec(compiled, namespace)  # noqa: S102 — isolated below
        except SandboxTimeoutError as exc:
            return buffer.getvalue(), f"timeout: {exc}"
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as exc:
            return buffer.getvalue(), (f"runtime error: {type(exc).__name__}: {exc}")

        return buffer.getvalue(), None

    @staticmethod
    def _exec_with_timeout(
        compiled: Any,
        namespace: dict[str, Any],
        timeout: int,
    ) -> None:
        # ``SIGALRM``/``setitimer`` exist on POSIX only; the caller guards with
        # ``hasattr(signal, "SIGALRM")`` so these are unreachable elsewhere.
        previous = signal.signal(signal.SIGALRM, _raise_timeout)  # type: ignore[attr-defined]
        signal.setitimer(  # type: ignore[attr-defined]
            signal.ITIMER_REAL,  # type: ignore[attr-defined]
            timeout,
        )
        try:
            exec(compiled, namespace)  # noqa: S102 — isolated below
        finally:
            signal.setitimer(  # type: ignore[attr-defined]
                signal.ITIMER_REAL,  # type: ignore[attr-defined]
                0,
            )
            signal.signal(signal.SIGALRM, previous)  # type: ignore[attr-defined]


def _raise_timeout(signum: int, frame: Any) -> None:
    raise SandboxTimeoutError("sandbox execution exceeded the timeout budget")
