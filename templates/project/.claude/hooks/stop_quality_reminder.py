#!/usr/bin/env python3
"""Lightweight Stop hook reminder for Claude Code."""

from pathlib import Path
import subprocess

root = Path.cwd()
gate = root / ".agent" / "quality-gates.md"
if gate.exists():
    print("Reminder: apply .agent/quality-gates.md before finalizing non-trivial work.")

drift = root / "scripts" / "check-doc-drift.py"
if drift.exists():
    subprocess.run(["python3", str(drift)], check=False)
