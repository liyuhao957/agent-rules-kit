#!/usr/bin/env python3
"""Stop hook: candidate-inbox gate plus advisory drift report.

Blocking scope is narrow and honest: the gate is that work must not finish
while `.agent/rule-candidates.md` holds pending candidates. That holds for the
current diff and for pending items that were committed without resolution —
committing is not a bypass. The doc-drift report is advisory and only shown
inside a block message. Set RULES_HOOK_ALLOW_PENDING=1 to bypass after
reviewing the candidate state.

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
IGNORED_CHANGED_PREFIXES = (".agent/work/", ".rules-kit/")
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
    files.update(git_files(["diff", "--no-renames", "--name-only", "--"]))
    files.update(git_files(["diff", "--no-renames", "--cached", "--name-only", "--"]))
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
        id_match = re.match(r"^###\s+([A-Za-z0-9_.:@+-]+)\s*$", raw.strip())
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
        # loop the gate.
        return 0

    root = Path.cwd()
    agent_dir = root / ".agent"
    if not agent_dir.exists():
        return 0

    if bypass_enabled():
        print("Rules hook bypass: RULES_HOOK_ALLOW_PENDING is set.")
        return 0

    nontrivial = nontrivial_files(changed_files())

    suggest = root / "scripts" / "suggest-rule-updates.py"
    if nontrivial and suggest.exists():
        # Refresh candidates from the current diff. Pending items from earlier
        # (including committed ones) are carried forward, never dropped.
        subprocess.run(["python3", str(suggest), "--quiet"], check=False)

    candidates_path = agent_dir / "rule-candidates.md"
    ids = pending_ids(candidates_path)
    if not ids:
        return 0

    if nontrivial:
        print(f"Rules hook blocked finalization: {len(ids)} pending rule candidate(s).", file=sys.stderr)
    else:
        print(
            f"Rules hook blocked finalization: {len(ids)} pending rule candidate(s) remain in "
            ".agent/rule-candidates.md from earlier (possibly committed) work. Committing does not resolve them.",
            file=sys.stderr,
        )
    for cid in ids[:MAX_LISTED_PENDING]:
        print(f"  - {cid}", file=sys.stderr)
    if len(ids) > MAX_LISTED_PENDING:
        print(f"  - ... {len(ids) - MAX_LISTED_PENDING} more", file=sys.stderr)
    print(
        "Resolve before finishing: open .agent/rule-candidates.md and mark each "
        "candidate promoted, checked-unchanged, rejected, or needs-user, with a real "
        "decision note. Re-check with: python3 scripts/suggest-rule-updates.py --quiet --check",
        file=sys.stderr,
    )
    print(
        "Bypass only after explicit review: RULES_HOOK_ALLOW_PENDING=1",
        file=sys.stderr,
    )

    if nontrivial:
        if (agent_dir / "quality-gates.md").exists():
            print("Also apply .agent/quality-gates.md before finalizing.", file=sys.stderr)
        drift = root / "scripts" / "check-doc-drift.py"
        if drift.exists():
            result = subprocess.run(
                ["python3", str(drift)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False
            )
            report = result.stdout.strip()
            if report:
                print("Advisory doc-drift report (non-blocking):", file=sys.stderr)
                print(report, file=sys.stderr)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
