from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
VENV = BACKEND / ".venv"
REQ = BACKEND / "requirements.txt"
STAMP = VENV / ".requirements.sha256"
PY = VENV / ("Scripts/python.exe" if sys.platform.startswith("win") else "bin/python")


def digest() -> str:
    return hashlib.sha256(REQ.read_bytes()).hexdigest()


def run(*args: str, cwd: Path | None = None) -> None:
    subprocess.check_call(list(args), cwd=str(cwd) if cwd else None)


print(f"[BharatStandards AI] Bootstrap Python: {sys.version.split()[0]}")

# Python 3.14 is supported by the current dependency set. The old project pinned
# Pydantic 2.11.x, whose pydantic-core/PyO3 combination did not support 3.14.
if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10 or newer is required.")

if not PY.exists():
    print(f"[BharatStandards AI] Creating virtual environment at {VENV}")
    run(sys.executable, "-m", "venv", str(VENV))

if not STAMP.exists() or STAMP.read_text(encoding="utf-8").strip() != digest():
    print("[BharatStandards AI] Installing/updating backend dependencies...")
    run(str(PY), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
    run(str(PY), "-m", "pip", "install", "-r", str(REQ))
    STAMP.write_text(digest(), encoding="utf-8")

print("[BharatStandards AI] Starting FastAPI on http://127.0.0.1:8000")
run(
    str(PY),
    "-m",
    "uvicorn",
    "app.main:app",
    "--reload",
    "--host",
    "127.0.0.1",
    "--port",
    "8000",
    cwd=BACKEND,
)
