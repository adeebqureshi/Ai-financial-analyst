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
SANDBOX_SOURCE_NAME: Final[str] = "<sandbox>"
_DEFAULT_TIMEOUT_SECONDS: Final[int] = 30
_KILL_GRACE_SECONDS: Final[int] = 5
class SandboxSecurityError(Exception):
class SandboxTimeoutError(TimeoutError):
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
    safe: dict[str, Any] = {}
    for name in _BASIC_BUILTIN_NAMES + _EXCEPTION_NAMES:
        safe[name] = getattr(builtins, name)
    for name in _MATH_FUNCTION_NAMES:
        safe[name] = getattr(math, name)
    safe.update(_MATH_CONSTANTS)
    return safe
SAFE_BUILTINS: Final[dict[str, Any]] = _build_safe_builtins()
_FORBIDDEN_NAMES: Final[frozenset[str]] = frozenset(
    {
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
        "open",
        "file",
        "exit",
        "quit",
        "help",
        "copyright",
        "credits",
        "license",
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
class SandboxValidator:
    def validate(self, code: str) -> str | None:
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
@dataclass(slots=True)
class SandboxResult:
    success: bool
    output: str
    error: str | None = None
    return_value: Any | None = None
class PythonSandbox:
    def __init__(
        self,
        timeout: int | None = None,
        memory_limit_mb: int | None = None,
    ) -> None:
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
    def validate(self, code: str) -> str | None:
        return SandboxValidator().validate(code)
    def run(
        self,
        code: str,
        context: dict[str, Any] | None = None,
        *,
        timeout: int | None = None,
    ) -> SandboxResult:
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
                    exec(compiled, namespace)
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
        previous = signal.signal(signal.SIGALRM, _raise_timeout)
        signal.setitimer(
            signal.ITIMER_REAL,
            timeout,
        )
        try:
            exec(compiled, namespace)
        finally:
            signal.setitimer(
                signal.ITIMER_REAL,
                0,
            )
            signal.signal(signal.SIGALRM, previous)
def _raise_timeout(signum: int, frame: Any) -> None:
    raise SandboxTimeoutError("sandbox execution exceeded the timeout budget")
def execute_untrusted(
    code: str,
    context: dict[str, Any] | None = None,
) -> SandboxResult:
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
    namespace = sandbox._build_namespace(context)
    output, error = sandbox._execute(compiled, namespace, None)
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
    project_root = Path(__file__).resolve().parent.parent.parent
    worker_script = project_root / "app" / "sandbox" / "worker.py"
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
    if proc is None or proc.poll() is not None:
        return
    try:
        proc.terminate()
    except OSError:
        pass
    try:
        proc.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), 9)
        except (AttributeError, OSError, ProcessLookupError):
            try:
                proc.kill()
            except OSError:
                pass
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            pass