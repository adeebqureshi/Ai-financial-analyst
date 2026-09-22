from __future__ import annotations
import pytest
from app.sandbox.executor import PythonSandbox
_SECRET_MARKERS = (
    "KEY", "SECRET", "TOKEN", "PASSWORD", "PASSWD",
    "CREDENTIAL", "IDENTITY", "APIKEY",
)
@pytest.fixture(scope="module")
def sandbox() -> PythonSandbox:
    return PythonSandbox()
def test_execution_runs_in_a_child_process(sandbox):
    assert "sandbox_marker" not in globals()
    result = sandbox.run("sandbox_marker = 1\nresult = 1")
    assert result.success
    assert "sandbox_marker" not in globals()
def test_host_modules_are_not_mutated_by_worker(sandbox):
    import sys
    before = set(sys.modules.keys())
    result = sandbox.run("result = 1")
    assert result.success
    assert set(sys.modules.keys()) == before
def test_infinite_loop_is_killed_by_parent(sandbox):
    result = sandbox.run("while True:\n    pass", timeout=2)
    assert not result.success
    assert "timeout" in result.error.lower()
def test_timeout_is_roughly_respected(sandbox):
    import time
    start = time.monotonic()
    sandbox.run("while True:\n    pass", timeout=2)
    elapsed = time.monotonic() - start
    assert elapsed < 15
@pytest.mark.parametrize(
    "code",
    [
        "result = open('/etc/passwd').read()",
        "result = open('C:/Windows/win.ini').read()",
        "import os\nresult = os.listdir('.')",
        "import pathlib\nresult = str(pathlib.Path.home())",
        "import tempfile\nresult = tempfile.gettempdir()",
        "import shutil\nresult = 1",
        "import glob\nresult = glob.glob('*')",
    ],
)
def test_filesystem_access_is_blocked(sandbox, code):
    result = sandbox.run(code)
    assert not result.success
def test_secret_env_vars_are_stripped(sandbox):
    sample = {
        "OPENAI_API_KEY": "sk-123",
        "AUTH_SECRET_KEY": "s3cret",
        "FMP_API_KEY": "top",
        "EDGAR_IDENTITY": "some-identity",
        "DATABASE_PASSWORD": "pw",
        "PATH": "C:\\Windows",
    }
    filtered = {
        k: v
        for k, v in sample.items()
        if not any(m in k.upper() for m in _SECRET_MARKERS)
    }
    assert "OPENAI_API_KEY" not in filtered
    assert "AUTH_SECRET_KEY" not in filtered
    assert "FMP_API_KEY" not in filtered
    assert "EDGAR_IDENTITY" not in filtered
    assert "DATABASE_PASSWORD" not in filtered
    assert filtered["PATH"] == "C:\\Windows"
@pytest.mark.parametrize(
    "code",
    [
        "import socket",
        "import urllib.request",
        "import urllib.parse",
        "import http.client",
        "import requests",
        "import ftplib",
        "import ssl",
        "result = __import__('socket')",
    ],
)
def test_network_access_is_blocked(sandbox, code):
    result = sandbox.run(code)
    assert not result.success
@pytest.mark.parametrize(
    "code",
    [
        "import subprocess\nresult = 1",
        "import multiprocessing\nresult = 1",
        "import os\nresult = os.system('echo hi')",
        "from subprocess import call\nresult = call(['echo', 'hi'])",
        "result = __import__('subprocess')",
    ],
)
def test_child_process_spawning_is_blocked(sandbox, code):
    result = sandbox.run(code)
    assert not result.success
@pytest.mark.parametrize(
    "code",
    [
        "result = eval('1+1')",
        "result = exec('1+1')",
        "result = compile('x', '<s>', 'exec')",
        "result = __import__('os')",
        "result = ''.__class__.__mro__",
        "result = (1).__class__",
        "result = __builtins__",
        "f = lambda: 1\nresult = f.__globals__",
        "result = globals()",
        "class X:\n    pass\nresult = X",
        "result = str.__class__.__base__.__subclasses__()",
    ],
)
def test_interpreter_escape_attempts_are_blocked(sandbox, code):
    result = sandbox.run(code)
    assert not result.success
def test_resource_limits_wiring_in_worker():
    try:
        import resource
    except ImportError:
        pytest.skip("resource module unavailable on this platform")
    from app.sandbox.worker import _apply_resource_limits
    _apply_resource_limits(cpu_seconds=None, memory_mb=None)
def test_memory_hog_aborts_instead_of_hanging():
    limited = PythonSandbox(memory_limit_mb=64)
    result = limited.run(
        "data = []\n"
        "for _ in range(1_000_000):\n"
        "    data.append('x' * 1024)\n"
        "result = len(data)\n",
        timeout=15,
    )
    assert result is not None