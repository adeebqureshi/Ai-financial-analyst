from __future__ import annotations

import ast
import builtins
import contextlib
import io
import json
import math
import os
import signal
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_CODE_LENGTH: Final[int] = 8000
"""Maximum number of characters of sandboxed code. Static cost guard."""

SANDBOX_SOURCE_NAME: Final[str] = "<sandbox>"

# Default wall-clock budget (seconds) when the caller passes none.
_DEFAULT_TIMEOUT_SECONDS: Final[int] = 30

# Extra grace (seconds) beyond the timeout before we hard-kill a worker.
_KILL_GRACE_SECONDS: Final[int] = 5


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

    def __init__(
        self,
        timeout: int | None = None,
        memory_limit_mb: int | None = None,
    ) -> None:
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb

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
        Validate and execute ``code`` inside an isolated subprocess worker.

        Args:
            code: The untrusted Python source to run.
            context: Explicit values the code may reference. Every value is
                injected into the worker namespace under its key; no other
                data (environment, filesystem, secrets) is visible to it.
            timeout: Optional override for the configured timeout. The worker
                is hard-killed if it exceeds the budget.

        Returns:
            A structured :class:`SandboxResult`. Exceptions never propagate.
        """
        reason = self.validate(code)
        if reason:
            return SandboxResult(
                success=False,
                output="",
                error=f"security: {reason}",
            )

        effective_timeout = timeout if timeout is not None and timeout > 0 else self.timeout
        effective_timeout = effective_timeout or _DEFAULT_TIMEOUT_SECONDS

        return _run_in_subprocess(
            code=code,
            context=context,
            timeout=effective_timeout,
            memory_limit_mb=self.memory_limit_mb,
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


# ─────────────────────────────────────────────────────────────────────────────
# Subprocess isolation
# ─────────────────────────────────────────────────────────────────────────────


def execute_untrusted(
    code: str,
    context: dict[str, Any] | None = None,
) -> SandboxResult:
    """
    Validate and execute ``code`` inline with the restricted namespace.

    This is the **worker-side** path: the untrusted code runs inside the
    already-isolated child process. It deliberately does *not* spawn another
    subprocess (avoiding recursion). The parent's kill-timer remains the hard
    safety net for timeouts/memory.

    Args:
        code: The untrusted Python source to run.
        context: Explicit values the code may reference.

    Returns:
        A structured :class:`SandboxResult`. Exceptions never propagate.
    """
    sandbox = PythonSandbox()

    reason = sandbox.validate(code)
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

    namespace = sandbox._build_namespace(context)  # noqa: SLF001 - internal worker path

    output, error = sandbox._execute(compiled, namespace, None)  # noqa: SLF001 - internal worker path

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


def _run_in_subprocess(
    *,
    code: str,
    context: dict[str, Any] | None,
    timeout: int,
    memory_limit_mb: int | None,
) -> SandboxResult:
    """
    Run ``code`` in a fresh, hard-killable worker process.

    The worker is spawned with a minimal, secret-free environment and an empty
    working directory. Input (code + context) is sent over stdin as JSON; the
    result is read back from stdout. If the worker exceeds ``timeout`` it is
    terminated and then forcibly killed (whole process group on POSIX).
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    worker_script = project_root / "app" / "sandbox" / "worker.py"

    # Spawn the worker with a secret-free environment.
    #
    # On POSIX we start from a minimal map. On Windows the interpreter needs
    # system variables (SYSTEMROOT, PATH, ...), so we start from a copy of the
    # current environment but strip everything that looks like a secret or a
    # provider credential. Either way the untrusted code never sees secrets.
    if os.name == "posix":
        worker_env: dict[str, str] | None = {
            "PYTHONPATH": str(project_root),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    else:
        worker_env = dict(os.environ)
        _SECRET_MARKERS = (
            "KEY", "SECRET", "TOKEN", "PASSWORD", "PASSWD",
            "CREDENTIAL", "IDENTITY", "APIKEY",
        )
        for _var in list(worker_env):
            _upper = _var.upper()
            if any(_marker in _upper for _marker in _SECRET_MARKERS):
                worker_env.pop(_var, None)
        worker_env["PYTHONPATH"] = str(project_root)
        worker_env["PYTHONIOENCODING"] = "utf-8"
        worker_env["PYTHONDONTWRITEBYTECODE"] = "1"

    payload = json.dumps(
        {
            "code": code,
            "context": context or {},
            "timeout": timeout,
            "memory_limit_mb": memory_limit_mb,
        }
    )

    working_dir = Path(tempfile.mkdtemp(prefix="sandbox-cwd-"))

    proc: subprocess.Popen | None = None

    try:
        proc = subprocess.Popen(
            [sys.executable, "-u", str(worker_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=worker_env,
            cwd=str(working_dir),
            start_new_session=True,
        )

        out_bytes, err_bytes = proc.communicate(
            input=payload.encode("utf-8"),
            timeout=timeout + _KILL_GRACE_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        _terminate_worker(proc, exc)
        out_bytes, err_bytes = proc.communicate() if proc is not None else (b"", b"")
        return SandboxResult(
            success=False,
            output="",
            error=f"timeout: sandbox execution exceeded {timeout}s and was terminated safely",
        )
    finally:
        if proc is not None and proc.poll() is None:
            _terminate_worker(proc, None)
        try:
            working_dir.rmdir()
        except OSError:
            pass

    if proc is None or proc.returncode != 0:
        stderr = ""
        if err_bytes:
            stderr = err_bytes.decode("utf-8", errors="replace").strip()
        logger.warning("Sandbox worker failed (exit=%s): %s",
                       proc.returncode if proc else "?", stderr)
        return SandboxResult(
            success=False,
            output="",
            error=f"sandbox process failed to execute code (exit {proc.returncode if proc else '?'})",
        )

    try:
        data = json.loads(out_bytes.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        logger.warning("Sandbox worker returned malformed output: %s",
                       err_bytes.decode("utf-8", errors="replace").strip())
        return SandboxResult(
            success=False,
            output="",
            error="sandbox produced no usable result",
        )

    return SandboxResult(
        success=bool(data.get("success")),
        output=data.get("output") or "",
        error=data.get("error"),
        return_value=data.get("return_value"),
    )


def _terminate_worker(proc: subprocess.Popen, _exc: Any) -> None:
    """
    Safely stop a runaway worker: terminate gracefully, then force-kill the
    whole process group so no descendant survives.
    """
    if proc is None or proc.poll() is not None:
        return

    try:
        proc.terminate()
    except OSError:
        pass

    # Give it a moment, then SIGKILL the process group (POSIX).
    try:
        proc.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), 9)  # type: ignore[attr-defined]
        except (AttributeError, OSError, ProcessLookupError):
            # Windows: no killpg / getpgid; fall back to kill().
            try:
                proc.kill()
            except OSError:
                pass
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            pass