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


def pending_candidates(path: Path) -> tuple[list[str], list[str]]:
    """Split pending candidates into (blocking, advisory).

    Only high-stakes `risk:*` candidates (secrets / billing / release / prod)
    block the Stop gate. Drift and command candidates are advisory: surfaced,
    never gated, so ordinary work is not taxed every session.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return [], []
    blocking: list[str] = []
    advisory: list[str] = []
    current_id: str | None = None
    current_kind = ""
    current_status = ""

    def flush() -> None:
        nonlocal current_id, current_kind, current_status
        if current_id and current_status == "pending":
            if current_kind == "risk" or current_id.startswith("risk:"):
                blocking.append(current_id)
            else:
                advisory.append(current_id)
        current_id, current_kind, current_status = None, "", ""

    for raw in text.splitlines():
        stripped = raw.strip()
        id_match = re.match(r"^###\s+([A-Za-z0-9_.:@+-]+)\s*$", stripped)
        if id_match:
            flush()
            current_id = id_match.group(1)
            continue
        if current_id:
            kind_match = re.match(r"^Kind:\s*(\S+)\s*$", stripped)
            if kind_match:
                current_kind = kind_match.group(1)
            status_match = re.match(r"^Status:\s*(\S+)\s*$", stripped)
            if status_match:
                current_status = status_match.group(1)
    flush()
    return blocking, advisory


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
    blocking, advisory = pending_candidates(candidates_path)

    if not blocking:
        # No high-stakes candidate. Surface advisory items in one line and let
        # the session end — ordinary drift never blocks.
        if advisory:
            print(
                f"Advisory: {len(advisory)} rule candidate(s) noted in .agent/rule-candidates.md "
                "(not blocking). Review when convenient: python3 scripts/suggest-rule-updates.py --check"
            )
        return 0

    print(
        f"Rules hook blocked finalization: {len(blocking)} pending high-risk rule candidate(s) "
        "(secrets/billing/release/prod). Committing does not resolve them.",
        file=sys.stderr,
    )
    for cid in blocking[:MAX_LISTED_PENDING]:
        print(f"  - {cid}", file=sys.stderr)
    if len(blocking) > MAX_LISTED_PENDING:
        print(f"  - ... {len(blocking) - MAX_LISTED_PENDING} more", file=sys.stderr)
    if advisory:
        print(f"  (+{len(advisory)} advisory candidate(s), not blocking)", file=sys.stderr)
    print(
        "Resolve each high-risk candidate in .agent/rule-candidates.md as promoted, "
        "checked-unchanged, rejected, or needs-user, with a real decision note. "
        "Re-check with: python3 scripts/suggest-rule-updates.py --quiet --check --gate",
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
