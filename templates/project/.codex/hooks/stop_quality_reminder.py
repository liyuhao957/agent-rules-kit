#!/usr/bin/env python3
"""Lightweight Stop hook reminder for Codex.

This hook intentionally does not block by default. It prints the shared quality
gate path and runs the doc-drift detector when available. Customize it per
project if you want hard enforcement.
"""

from pathlib import Path
import subprocess

root = Path.cwd()
gate = root / ".agent" / "quality-gates.md"
if gate.exists():
    print("Reminder: apply .agent/quality-gates.md before finalizing non-trivial work.")

drift = root / "scripts" / "check-doc-drift.py"
if drift.exists():
    subprocess.run(["python3", str(drift)], check=False)
