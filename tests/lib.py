"""Shared helpers for the Relay Rules test suite (stdlib only)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT / "templates" / "project"
BASH_GUARD = TEMPLATE / ".claude" / "hooks" / "pre_bash_release_guard.py"
STOP_HOOK = TEMPLATE / ".claude" / "hooks" / "stop_quality_reminder.py"


def run_hook(hook_path: Path, payload: object, cwd: Path | None = None, env: dict | None = None):
    """Run a hook with a JSON payload on stdin. Returns (exit_code, stdout, stderr)."""
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    proc = subprocess.run(
        [sys.executable, str(hook_path)],
        input=raw,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def bash_payload(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


class Results:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.failures: list[str] = []

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        if ok:
            self.passed += 1
        else:
            self.failed += 1
            self.failures.append(f"{name}: {detail}".rstrip(": "))

    def report(self, suite: str) -> int:
        total = self.passed + self.failed
        status = "OK" if self.failed == 0 else "FAIL"
        print(f"[{status}] {suite}: {self.passed}/{total} passed")
        for failure in self.failures:
            print(f"    - {failure}")
        return 0 if self.failed == 0 else 1
