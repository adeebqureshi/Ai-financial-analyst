"""Launch Docker services (PostgreSQL + Redis) and integration tests as detached processes."""
import subprocess
import sys
import time
import os

ROOT = r"C:\Users\ASUS\Desktop\ai-financial-analyst"
PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")

# 1. Start Docker services
with open(os.path.join(ROOT, "docker_start.log"), "w") as f:
    subprocess.Popen(
        ["docker", "compose", "-f", "docker/docker-compose.yml", "up", "-d", "postgres", "redis"],
        stdout=f,
        stderr=subprocess.STDOUT,
        cwd=ROOT,
        creationflags=0x00000008 | 0x00000200,
    )

open(os.path.join(ROOT, "docker_started.txt"), "w").write("launched docker compose")
