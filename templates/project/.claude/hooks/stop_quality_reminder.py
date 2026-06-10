#!/usr/bin/env python3
"""Stop hook: candidate-inbox gate plus advisory drift report.

Blocking scope is narrow and honest: the only mechanical gate is that
non-trivial git changes must not leave `.agent/rule-candidates.md` with
pending candidates. The doc-drift report is advisory and never blocks.
Set RULES_HOOK_ALLOW_PENDING=1 to bypass after reviewing the candidate state.

Works for both Claude Code and Codex Stop hooks: on both, exit code 2 with a
stderr reason tells the agent to continue and resolve the listed candidates.
The stdin payload's `stop_hook_active` flag breaks continuation loops.
"""

from __future__ import annotations

import json
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
MAX_LISTED_PENDING = 8


def bypass_enabled() -> bool:
    return os.environ.get("RULES_HOOK_ALLOW_PENDING", "").strip().lower() in TRUE_VALUES


def stdin_payload() -> dict:
    try:
        raw = sys.stdin.read()
    except OSError:
        return {}
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def git_files(args: list[str]) -> set[str]:
    result = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
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


def pending_ids(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    ids: list[str] = []
    current_id: str | None = None
    for raw in text.splitlines():
        id_match = re.match(r"^###\s+([A-Za-z0-9_.:-]+)", raw.strip())
        if id_match:
            current_id = id_match.group(1)
            continue
        if current_id and re.match(r"^Status:\s*pending\s*$", raw.strip()):
            ids.append(current_id)
            current_id = None
    return ids


def main() -> int:
    payload = stdin_payload()
    if payload.get("stop_hook_active"):
        # A previous Stop block already asked the agent to act once. Do not
        # loop the gate; the advisory output below already ran last time.
        return 0

    root = Path.cwd()
    agent_dir = root / ".agent"

    nontrivial = nontrivial_files(changed_files())
    if not nontrivial:
        return 0

    if (root / ".agent" / "quality-gates.md").exists():
        print("Reminder: apply .agent/quality-gates.md before finalizing non-trivial work.", flush=True)

    drift = root / "scripts" / "check-doc-drift.py"
    if drift.exists():
        print("Advisory doc-drift report (non-blocking):", flush=True)
        subprocess.run(["python3", str(drift)], check=False)

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

    candidates_path = root / ".agent" / "rule-candidates.md"
    ids = pending_ids(candidates_path)
    print(f"Rules hook blocked finalization: {len(ids)} pending rule candidate(s).", file=sys.stderr)
    for cid in ids[:MAX_LISTED_PENDING]:
        print(f"  - {cid}", file=sys.stderr)
    if len(ids) > MAX_LISTED_PENDING:
        print(f"  - ... {len(ids) - MAX_LISTED_PENDING} more", file=sys.stderr)
    print(
        "Resolve before finishing: open .agent/rule-candidates.md and mark each "
        "candidate promoted, checked-unchanged, rejected, or needs-user based on "
        "current evidence. Re-check with: python3 scripts/suggest-rule-updates.py --quiet --check",
        file=sys.stderr,
    )
    print(
        "Bypass only after explicit review: RULES_HOOK_ALLOW_PENDING=1",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
