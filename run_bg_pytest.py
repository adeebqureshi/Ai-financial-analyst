import subprocess
import sys

ROOT = r"C:\Users\ASUS\Desktop\ai-financial-analyst"
PY = ROOT + r"\.venv\Scripts\python.exe"

target = sys.argv[1] if len(sys.argv) > 1 else "tests/infrastructure"
xml = sys.argv[2] if len(sys.argv) > 2 else "junit_infra.xml"

with open(ROOT + "\\bg_run.log", "w") as out:
    subprocess.Popen(
        [PY, "-m", "pytest", target, "-q", "-p", "no:warnings", "--junitxml=" + xml],
        stdout=out,
        stderr=subprocess.STDOUT,
        cwd=ROOT,
        creationflags=0x00000008 | 0x00000200,
    )

open(ROOT + "\\bg_launch.txt", "w").write("launched " + target)
