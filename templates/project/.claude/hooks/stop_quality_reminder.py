#!/usr/bin/env python3
"""Stop hook reminder and optional strict quality gate for coding agents.

Runs doc drift discovery and blocks finalization when non-trivial git changes
still leave `.agent/rule-candidates.md` with pending candidates.
Set RULES_HOOK_ALLOW_PENDING=1 to bypass after reviewing the candidate state.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys


TRUE_VALUES = {"1", "true", "yes", "allow", "bypass"}
IGNORED_CHANGED_FILES = {
    ".agent/bootstrap-report.md",
    ".agent/project-map.md",
    ".agent/rule-candidates.md",
}
IGNORED_CHANGED_PREFIXES = (".agent/work/",)


def bypass_enabled() -> bool:
    return os.environ.get("RULES_HOOK_ALLOW_PENDING", "").strip().lower() in TRUE_VALUES


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)


def git_files(args: list[str]) -> set[str]:
    result = run(["git", *args])
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def changed_files() -> set[str]:
    files: set[str] = set()
    files.update(git_files(["diff", "--name-only", "--"]))
    files.update(git_files(["diff", "--cached", "--name-only", "--"]))
    files.update(git_files(["ls-files", "--others", "--exclude-standard"]))
    return files


def nontrivial_files(files: set[str]) -> list[str]:
    kept: list[str] = []
    for file_path in sorted(files):
        if file_path in IGNORED_CHANGED_FILES:
            continue
        if any(file_path.startswith(prefix) for prefix in IGNORED_CHANGED_PREFIXES):
            continue
        kept.append(file_path)
    return kept


def pending_count(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return 0
    return len(re.findall(r"^Status:\s*pending\s*$", text, flags=re.MULTILINE))


def main() -> int:
    root = Path.cwd()
    agent_dir = root / ".agent"
    gate = root / ".agent" / "quality-gates.md"
    if gate.exists():
        print("Reminder: apply .agent/quality-gates.md before finalizing non-trivial work.")

    nontrivial = nontrivial_files(changed_files())

    drift = root / "scripts" / "check-doc-drift.py"
    if drift.exists():
        subprocess.run(["python3", str(drift)], check=False)

    if not nontrivial:
        return 0

    if not agent_dir.exists():
        print("Rules hook warning: .agent is missing; pending candidates were not enforced.")
        return 0

    if bypass_enabled():
        print("Rules hook bypass: RULES_HOOK_ALLOW_PENDING is set.")
        return 0

    suggest = root / "scripts" / "suggest-rule-updates.py"
    if not suggest.exists():
        print("Rules hook warning: scripts/suggest-rule-updates.py is missing; pending candidates were not enforced.")
        return 0

    result = subprocess.run(["python3", str(suggest), "--quiet", "--check"], check=False)
    if result.returncode == 0:
        return 0

    candidates = root / ".agent" / "rule-candidates.md"
    pending = pending_count(candidates)
    print("Rules hook blocked finalization.", file=sys.stderr)
    print(f"- Non-trivial changed files detected: {len(nontrivial)}", file=sys.stderr)
    print(f"- Pending rule candidates detected: {pending}", file=sys.stderr)
    print(
        "Review .agent/rule-candidates.md and mark each candidate promoted, "
        "checked-unchanged, rejected, or needs-user before finalizing.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
