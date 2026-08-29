"""Launch Docker services, wait for readiness, then run integration tests.

This script runs as a detached background process and writes output to
integration_test_results.log.
"""
import subprocess
import sys
import time
import os

ROOT = r"C:\Users\ASUS\Desktop\ai-financial-analyst"
PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")

LOG_PATH = os.path.join(ROOT, "integration_test_results.log")
log = open(LOG_PATH, "w")

def run(cmd, timeout=60, check=False):
    """Run a command and return its CompletedProcess."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=timeout,
        shell=isinstance(cmd, str),
    )
    if check and result.returncode != 0:
        log.write(f"Command failed: {cmd}\nstdout: {result.stdout}\nstderr: {result.stderr}\n")
    return result

# 1. Start Docker Desktop if not running
log.write("=== Starting Docker services ===\n")
log.flush()

try:
    result = run(["docker", "ps"], timeout=15)
    if result.returncode != 0:
        log.write("Docker not responding. Attempting to start Docker Desktop...\n")
        log.flush()
        # Try to start Docker Desktop
        subprocess.Popen(
            ["cmd", "/c", "start", "Docker Desktop",
             r"C:\Program Files\Docker\Docker\resources\docker-desktop.exe"],
            creationflags=0x00000008 | 0x00000200,
        )
        # Wait for Docker to start (up to 120 seconds)
        for i in range(60):
            time.sleep(2)
            result = run(["docker", "ps"], timeout=10)
            if result.returncode == 0:
                log.write(f"Docker is ready after {i*2} seconds\n")
                break
        else:
            log.write("Docker did not become ready.\n")
    else:
        log.write("Docker is already running.\n")
except Exception as e:
    log.write(f"Docker check error: {e}\n")

# 2. Start compose services
try:
    result = run(
        ["docker", "compose", "-f", "docker/docker-compose.yml", "up", "-d", "--wait", "postgres", "redis"],
        timeout=120
    )
    log.write(f"docker compose up: returncode={result.returncode}\n")
    if result.stdout:
        log.write(result.stdout + "\n")
    if result.stderr:
        log.write(result.stderr + "\n")
except Exception as e:
    log.write(f"docker compose up error: {e}\n")

# 3. Wait for health checks
for i in range(60):
    time.sleep(2)
    result = run(["docker", "compose", "-f", "docker/docker-compose.yml", "ps", "--format", "{{.Service}}:{{.Status}}"], timeout=15)
    if result.returncode == 0:
        log.write(f"Service status: {result.stdout.strip()}\n")
        if "healthy" in result.stdout.lower() and "starting" not in result.stdout.lower():
            log.write("Services are healthy!\n")
            break
    log.flush()

# 4. Run integration tests
log.write("\n=== Running integration tests ===\n")
log.flush()

env = os.environ.copy()
env["TEST_POSTGRES_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5432/financial"
env["TEST_REDIS_URL"] = "redis://localhost:6379/0"

result = subprocess.run(
    [PY, "-m", "pytest",
     "tests/infrastructure/test_integration_services.py",
     "-v", "-p", "no:warnings"],
    capture_output=True,
    text=True,
    cwd=ROOT,
    env=env,
    timeout=120,
)

log.write(f"Integration test returncode: {result.returncode}\n")
log.write(result.stdout)
if result.stderr:
    log.write(result.stderr)
log.flush()

# 5. Run full test suite
log.write("\n=== Running full test suite ===\n")
log.flush()

result = subprocess.run(
    [PY, "-m", "pytest", "-q", "-p", "no:warnings"],
    capture_output=True,
    text=True,
    cwd=ROOT,
    env=env,
    timeout=600,
)

log.write(f"Full test suite returncode: {result.returncode}\n")
log.write(result.stdout)
if result.stderr:
    log.write(result.stderr)
log.flush()

log.write("\n=== DONE ===\n")
log.flush()
log.close()
