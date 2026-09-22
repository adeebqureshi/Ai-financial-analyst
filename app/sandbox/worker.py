from __future__ import annotations
import json
import sys
def _apply_resource_limits(
    cpu_seconds: int | None,
    memory_mb: int | None,
    timeout_cls: type,
) -> None:
    try:
        import resource
        import signal as _signal
    except ImportError:
        return
    if cpu_seconds and cpu_seconds > 0:
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (cpu_seconds, cpu_seconds),
        )
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
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    return repr(value)
def _write_result(*, success, output, error, return_value=None) -> None:
    envelope = {
        "success": bool(success),
        "output": output or "",
        "error": error,
        "return_value": _serialize_value(return_value) if success else None,
    }
    sys.stdout.write(json.dumps(envelope, default=str))
    sys.stdout.flush()
def main() -> int:
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
    except Exception as exc:
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
if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        _write_result(
            success=False,
            output="",
            error=f"sandbox worker crashed: {type(exc).__name__}: {exc}",
        )
        sys.exit(1)