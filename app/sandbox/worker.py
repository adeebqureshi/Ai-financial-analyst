"""
worker.py

Subprocess sandbox worker.

This module is the **entry point** of the isolated child process that executes
LLM-generated (untrusted) Python. It is never imported by the application's
FastAPI process directly; instead the parent spawns it as a fresh subprocess
per execution.

Why a subprocess worker?
    A separate process means a runaway program (infinite loop, memory blowup)
    can be hard-killed by the parent with ``SIGKILL``/``Process.kill()``. This
    closes the in-process ``exec()`` hole where an infinite loop could not be
    interrupted on platforms without ``SIGALRM`` (e.g. Windows).

What this worker does
    - Reads one JSON request ``{code, context, timeout, memory_limit_mb}``
      from stdin.
    - Applies OS-level resource limits (POSIX ``resource.setrlimit``):
      CPU seconds, virtual-memory ceiling, no child processes, a small file
      descriptor budget and no file writes. On non-POSIX platforms these are
      best-effort (the parent's hard kill-timer is the guaranteed bound).
    - Executes the untrusted code through the same restricted namespace and
      AST validation used by the (previously in-process) sandbox.
    - Writes one JSON result ``{success, output, error, return_value}`` to
      stdout and exits.

Security contract
    - The worker receives **only** the untrusted code, an explicit ``context``
      dict and resource budgets. It never sees the application's environment,
      secrets, database connections or filesystem.
    - The host spawns the worker with a minimal, secret-free environment and a
      fresh, empty working directory, restricting filesystem and secret access.
"""

from __future__ import annotations

import json
import sys



def _apply_resource_limits(
    cpu_seconds: int | None,
    memory_mb: int | None,
    timeout_cls: type,
) -> None:
    """
    Apply OS-level resource limits before executing untrusted code.

    On POSIX these are enforced by the kernel (``resource.setrlimit``). On
    Windows the ``resource`` module is unavailable and limits are best-effort:
    the parent process hard-kills the worker when it exceeds its time budget,
    which bounds both runaway CPU and runaway memory in practice.
    """
    try:
        import resource
        import signal as _signal
    except ImportError:  # non-POSIX: the parent kill-timer is the safety net
        return

    if cpu_seconds and cpu_seconds > 0:
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (cpu_seconds, cpu_seconds),
        )

        # Turn the kernel's SIGXCPU into a structured timeout error instead of
        # a silent kill, so a CPU-bound runaway reports "timeout" cleanly.
        def _on_sigxcpu(_signum, _frame):
            raise timeout_cls("sandbox execution exceeded the CPU time limit")

        try:
            _signal.signal(_signal.SIGXCPU, _on_sigxcpu)
        except (AttributeError, ValueError, OSError):
            pass

    if memory_mb and memory_mb > 0:
        memory_bytes = memory_mb * 1024 * 1024
        try:
            resource.setrlimit(
                resource.RLIMIT_AS,
                (memory_bytes, memory_bytes),
            )
        except (ValueError, OSError):
            pass

    try:
        resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
    except (ValueError, OSError):
        pass

    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))
    except (ValueError, OSError):
        pass

    try:
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    except (ValueError, OSError):
        pass


def _serialize_value(value):
    """Return a JSON-safe snapshot of a sandbox result value."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    return repr(value)


def _write_result(*, success, output, error, return_value=None) -> None:
    """Emit the single JSON result envelope to stdout."""
    envelope = {
        "success": bool(success),
        "output": output or "",
        "error": error,
        "return_value": _serialize_value(return_value) if success else None,
    }
    sys.stdout.write(json.dumps(envelope, default=str))
    sys.stdout.flush()


def main() -> int:
    """Read a request from stdin, execute it, and emit a JSON result."""
    try:
        raw = sys.stdin.read()
        if not raw:
            raise ValueError("empty request")
        payload = json.loads(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        _write_result(
            success=False,
            output="",
            error=f"sandbox worker rejected request: {exc}",
        )
        return 2

    code = payload.get("code", "")
    context = payload.get("context") or {}
    timeout = payload.get("timeout")
    memory_mb = payload.get("memory_limit_mb")

    try:
        from app.sandbox.executor import SandboxTimeoutError, execute_untrusted
    except Exception as exc:  # pragma: no cover - hostile environment
        _write_result(
            success=False,
            output="",
            error=f"sandbox worker failed to initialise: {exc}",
        )
        return 3

    _apply_resource_limits(
        cpu_seconds=int(timeout) if timeout else None,
        memory_mb=int(memory_mb) if memory_mb else None,
        timeout_cls=SandboxTimeoutError,
    )

    result = execute_untrusted(code, context)

    _write_result(
        success=result.success,
        output=result.output,
        error=result.error,
        return_value=result.return_value if result.success else None,
    )

    return 0


if __name__ == "__main__":  # pragma: no cover - executed as a subprocess
    try:
        sys.exit(main())
    except Exception as exc:  # pragma: no cover - last-resort safety net
        _write_result(
            success=False,
            output="",
            error=f"sandbox worker crashed: {type(exc).__name__}: {exc}",
        )
        sys.exit(1)