"""Launch full test suite as a detached background process."""
import subprocess
import sys
import os

ROOT = r"C:\Users\ASUS\Desktop\ai-financial-analyst"
PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")

# Allow integration tests to run against local Docker services
env = os.environ.copy()
env["TEST_POSTGRES_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5432/financial"
env["TEST_REDIS_URL"] = "redis://localhost:6379/0"

xml = sys.argv[1] if len(sys.argv) > 1 else "junit_full.xml"

with open(os.path.join(ROOT, "full_run.log"), "w") as out:
    subprocess.Popen(
        [PY, "-m", "pytest", "-q", "-p", "no:warnings", "--junitxml=" + xml],
        stdout=out,
        stderr=subprocess.STDOUT,
        cwd=ROOT,
        env=env,
        creationflags=0x00000008 | 0x00000200,
    )

open(os.path.join(ROOT, "full_run_started.txt"), "w").write("launched full test suite")
