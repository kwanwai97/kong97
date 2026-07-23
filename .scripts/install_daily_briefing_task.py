"""Windows daily briefing helper: create a scheduled task that runs at 00:05."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
SCRIPT = ROOT / ".scripts" / "daily_briefing.py"
TASK_NAME = "DigitalTwin_DailyBriefing"


def main() -> int:
    if not PYTHON.exists():
        print(f"MISSING_PYTHON {PYTHON}")
        return 1
    cmd = [
        "schtasks",
        "/Create",
        "/TN", TASK_NAME,
        "/TR", f'"{PYTHON}" "{SCRIPT}"',
        "/SC", "DAILY",
        "/ST", "00:05",
        "/F",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    print(p.stdout.strip())
    print(p.stderr.strip())
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
