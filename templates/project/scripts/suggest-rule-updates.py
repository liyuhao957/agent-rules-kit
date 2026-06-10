#!/usr/bin/env python3
"""Generate rule-maintenance candidates from current project evidence.

The script writes candidates to .agent/rule-candidates.md. It never promotes
candidates into official rules. Agents must inspect evidence and mark each item
promoted, checked-unchanged, rejected, or needs-user before finalizing work.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_STATUSES = {"pending", "promoted", "checked-unchanged", "rejected", "needs-user"}
UNRESOLVED_STATUSES = {"pending"}

# Kit-generated files must not create candidates about themselves.
GENERATED_FILES = {
    ".agent/bootstrap-report.md",
    ".agent/project-map.md",
    ".agent/rule-candidates.md",
}
GENERATED_PREFIXES = (".agent/work/",)


def run_git(args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def changed_files(base: str | None) -> list[str]:
    files: set[str] = set()
    if base:
        files.update(run_git(["diff", "--name-only", base, "--"]))
    else:
        files.update(run_git(["diff", "--name-only", "--"]))
        files.update(run_git(["diff", "--cached", "--name-only", "--"]))
    files.update(run_git(["ls-files", "--others", "--exclude-standard"]))
    kept = [
        f
        for f in files
        if f not in GENERATED_FILES and not any(f.startswith(p) for p in GENERATED_PREFIXES)
    ]
    return sorted(kept)


def read_text(path: Path, limit: int = 200_000) -> str:
    try:
        return path.read_bytes()[:limit].decode("utf-8", errors="replace")
    except OSError:
        return ""


def matches(pattern: str, file_path: str) -> bool:
    normalized = file_path.replace("\\", "/")
    return fnmatch.fnmatch(normalized, pattern.replace("\\", "/"))


def parse_drift_map(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []

    rules: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    active_list: str | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        if re.match(r"^\s*-\s+name:\s*", line):
            if current:
                rules.append(current)
            current = {
                "name": line.split("name:", 1)[1].strip().strip('"'),
                "paths": [],
                "docs": [],
                "reason": "",
            }
            active_list = None
            continue

        if current is None:
            continue

        stripped = line.strip()
        if stripped in {"paths:", "docs:"}:
            active_list = stripped[:-1]
            continue

        if stripped.startswith("reason:"):
            current["reason"] = stripped.split("reason:", 1)[1].strip().strip('"')
            active_list = None
            continue

        if stripped.startswith("- ") and active_list in {"paths", "docs"}:
            current[active_list].append(stripped[2:].strip().strip('"'))  # type: ignore[index]

    if current:
        rules.append(current)
    return rules


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip().lower()).strip("-")
    return slug[:80] or "candidate"


def existing_statuses(path: Path) -> dict[str, str]:
    statuses: dict[str, str] = {}
    text = read_text(path)
    current_id: str | None = None
    for raw in text.splitlines():
        id_match = re.match(r"^###\s+([A-Za-z0-9_.:-]+)", raw.strip())
        if id_match:
            current_id = id_match.group(1)
            continue
        status_match = re.match(r"^Status:\s*([A-Za-z-]+)\s*$", raw.strip())
        if current_id and status_match:
            status = status_match.group(1)
            if status in ALLOWED_STATUSES:
                statuses[current_id] = status
    return statuses


def existing_notes(path: Path) -> dict[str, list[str]]:
    notes: dict[str, list[str]] = {}
    text = read_text(path)
    current_id: str | None = None
    in_notes = False
    current_notes: list[str] = []
    for raw in text.splitlines():
        id_match = re.match(r"^###\s+([A-Za-z0-9_.:-]+)", raw.strip())
        if id_match:
            if current_id is not None:
                notes[current_id] = current_notes
            current_id = id_match.group(1)
            in_notes = False
            current_notes = []
            continue
        if current_id is None:
            continue
        if raw.strip() == "Decision notes:":
            in_notes = True
            current_notes = []
            continue
        if in_notes and raw.startswith("### "):
            notes[current_id] = current_notes
            in_notes = False
            current_notes = []
            continue
        if in_notes:
            if raw.strip() == "":
                in_notes = False
            else:
                current_notes.append(raw)
    if current_id is not None:
        notes[current_id] = current_notes
    return notes


def drift_candidates(files: list[str]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    rules = parse_drift_map(Path(".agent/drift-map.yml"))
    for rule in rules:
        patterns = rule.get("paths", [])
        matched = [
            file_path
            for file_path in files
            if any(matches(str(pattern), file_path) for pattern in patterns)  # type: ignore[arg-type]
        ]
        if not matched:
            continue
        name = str(rule.get("name", "unnamed"))
        docs = [str(doc) for doc in rule.get("docs", [])]  # type: ignore[arg-type]
        candidates.append(
            {
                "id": f"drift:{slugify(name)}",
                "title": f"Review rule docs for changed {name} paths",
                "kind": "drift",
                "default_status": "pending",
                "evidence": matched[:20],
                "docs": docs,
                "action": "Agent should inspect changed files and decide whether to update, keep unchanged, or reject rule changes.",
                "reason": str(rule.get("reason", "")),
            }
        )
    return candidates


def command_candidate_rows() -> list[tuple[str, str]]:
    text = read_text(Path(".agent/command-contract.md"))
    rows: list[tuple[str, str]] = []
    in_block = False
    for raw in text.splitlines():
        if raw.strip() == "# BEGIN GENERATED COMMAND CANDIDATES":
            in_block = True
            continue
        if raw.strip() == "# END GENERATED COMMAND CANDIDATES":
            in_block = False
            continue
        if not in_block or not raw.startswith("|") or "`" not in raw:
            continue
        parts = [part.strip() for part in raw.strip().strip("|").split("|")]
        if len(parts) < 2 or parts[0] in {"Purpose", "---"}:
            continue
        command_match = re.search(r"`([^`]+)`", parts[1])
        if command_match:
            rows.append((parts[0], command_match.group(1)))
    return rows


def command_inventory_has(command: str) -> bool:
    text = read_text(Path(".agent/command-contract.md"))
    before = text.split("## Auto-Detected Command Candidates", 1)[0]
    return command in before


def command_candidates() -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for purpose, command in command_candidate_rows():
        if command_inventory_has(command):
            continue
        candidates.append(
            {
                "id": f"command:{slugify(command)}",
                "title": f"Decide whether `{command}` should be promoted to command inventory",
                "kind": "command",
                "default_status": "pending",
                "evidence": [f"{purpose}: {command}"],
                "docs": [".agent/command-contract.md", ".agent/domains/build-test.md"],
                "action": "Agent should verify whether this command is durable enough to promote, otherwise mark checked-unchanged or rejected.",
                "reason": "Generated command candidate is not yet present in the verified command inventory.",
            }
        )
    return candidates


def backup_candidates() -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    backup_root = Path(".rules-kit/backups")
    if not backup_root.exists():
        return candidates
    for path in sorted(backup_root.glob("rules-install-*/*")):
        if path.name not in {"AGENTS.md", "CLAUDE.md"}:
            continue
        text = read_text(path, limit=80_000)
        headings = [line.strip() for line in text.splitlines() if line.startswith("#")][:20]
        candidates.append(
            {
                "id": f"backup:{slugify(str(path))}",
                "title": f"Review old rule backup `{path.as_posix()}`",
                "kind": "backup",
                "default_status": "pending",
                "evidence": headings or ["no markdown headings found"],
                "docs": [".agent/product-invariants.md", ".agent/user-journeys.md", ".agent/domains/"],
                "action": "Agent should mine useful durable facts from the backup, reject stale details, and mark high-risk unverified facts as needs-user.",
                "reason": "Old rule files may contain useful project-specific facts but may also be stale or wrong.",
            }
        )
    return candidates


def segmentize(path: str) -> str:
    """Lowercase a path with camelCase boundaries turned into separators.

    "src/ProductCard.tsx" -> "src/product-card.tsx" so word-boundary regexes
    can tell "prod" (deploy target) apart from "Product" (domain noun).
    """
    split_camel = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", path)
    split_acronym = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "-", split_camel)
    return split_acronym.lower()


# Word-boundary patterns applied to segmentized paths. Raw substring matching
# is forbidden here: "prod" must not match ProductCard.tsx, "cloud" must not
# match cloudinaryHelper.ts. Boundaries are path/word separators: / _ . -
_B = r"(^|[-_./])"
_E = r"([-_./]|$)"
HIGH_RISK_PATTERNS = {
    "release": (
        rf"{_B}fastlane{_E}",
        r"(^|/)\.github/workflows(/|$)",
        rf"{_B}deploy(ment)?s?{_E}",
        rf"{_B}signing{_E}",
        r"\.entitlements$",
        rf"{_B}export-?options\.plist$",
        rf"{_B}helm{_E}",
        rf"{_B}terraform{_E}",
    ),
    "secrets": (
        r"(^|/)\.env([-_.]|$)",
        rf"{_B}secrets?{_E}",
        rf"{_B}credentials?{_E}",
        r"private[-_]?key",
        rf"{_B}api[-_]?keys?{_E}",
    ),
    "remote": (
        rf"{_B}prod(uction)?{_E}",
        rf"{_B}firebase{_E}",
        rf"{_B}supabase{_E}",
        rf"{_B}s3{_E}",
        rf"{_B}remote{_E}",
    ),
    "billing": (
        rf"{_B}pricing{_E}",
        rf"{_B}billing{_E}",
        rf"{_B}subscriptions?{_E}",
        rf"{_B}purchases?{_E}",
        rf"{_B}revenue{_E}",
        rf"{_B}paywall{_E}",
        rf"{_B}iap{_E}",
    ),
}


def risk_candidates(files: list[str]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for name, patterns in HIGH_RISK_PATTERNS.items():
        matched = [
            file_path
            for file_path in files
            if any(re.search(pattern, segmentize(file_path)) for pattern in patterns)
        ]
        if not matched:
            continue
        candidates.append(
            {
                "id": f"risk:{name}",
                "title": f"Classify high-risk {name} rule impact",
                "kind": "risk",
                "default_status": "pending",
                "evidence": matched[:20],
                "docs": [".agent/tool-policy.md", ".agent/domains/release.md", ".agent/adaptation-review.md"],
                "action": "Agent should verify from current repo/tool evidence. If not provable, mark needs-user and record the uncertainty without asking unless this task depends on it.",
                "reason": "High-risk areas must not be inferred from filenames or stale docs.",
            }
        )
    return candidates


def all_candidates(files: list[str]) -> list[dict[str, object]]:
    seen: set[str] = set()
    candidates: list[dict[str, object]] = []
    for group in (drift_candidates(files), command_candidates(), backup_candidates(), risk_candidates(files)):
        for candidate in group:
            cid = str(candidate["id"])
            if cid in seen:
                continue
            seen.add(cid)
            candidates.append(candidate)
    return candidates


def render(candidates: list[dict[str, object]], statuses: dict[str, str], notes: dict[str, list[str]]) -> str:
    lines = [
        "# Rule Candidates",
        "",
        "This file is the automatic-growth inbox for project rules. Scripts generate candidates here; Claude/Codex agents decide and update official `.agent/*` docs when warranted.",
        "",
        "Rules must not grow by blindly copying scanner output into durable docs. The agent should inspect current code/config/tool evidence, then choose one status for each candidate:",
        "",
        "- `promoted`: verified durable fact was added to the appropriate `.agent/*` doc.",
        "- `checked-unchanged`: reviewed evidence and existing rules still cover it.",
        "- `rejected`: not durable, too specific, obvious from code, or not useful as a rule.",
        "- `needs-user`: high-risk fact cannot be proven from repo/tool evidence. Record the uncertainty; do not ask the user unless the current task depends on it.",
        "- `pending`: not yet handled. Do not finalize non-trivial work with pending candidates.",
        "",
        "Agent rule: decide autonomously whenever current evidence is enough. Do not ask the user to classify ordinary candidates.",
        "",
        "# BEGIN GENERATED RULE CANDIDATES",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
    ]
    if not candidates:
        lines.append("- no current candidates")
    for candidate in candidates:
        cid = str(candidate["id"])
        status = statuses.get(cid, str(candidate.get("default_status", "pending")))
        if status not in ALLOWED_STATUSES:
            status = "pending"
        lines.extend(
            [
                f"### {cid}",
                f"Status: {status}",
                f"Kind: {candidate.get('kind', 'unknown')}",
                f"Title: {candidate.get('title', '')}",
                f"Reason: {candidate.get('reason', '')}",
                "Evidence:",
            ]
        )
        for item in candidate.get("evidence", []):  # type: ignore[assignment]
            lines.append(f"- `{item}`")
        lines.append("Review docs:")
        for doc in candidate.get("docs", []):  # type: ignore[assignment]
            lines.append(f"- `{doc}`")
        lines.extend(
            [
                f"Agent action: {candidate.get('action', '')}",
                "Decision notes:",
            ]
        )
        candidate_notes = notes.get(cid)
        if candidate_notes and candidate_notes != ["- pending"]:
            lines.extend(candidate_notes)
        else:
            lines.append("- pending")
        lines.append("")
    lines.append("# END GENERATED RULE CANDIDATES")
    return "\n".join(lines).rstrip() + "\n"


def unresolved_count(path: Path) -> int:
    text = read_text(path)
    return len(re.findall(r"^Status:\s*pending\s*$", text, flags=re.MULTILINE))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or validate rule update candidates.")
    parser.add_argument("--base", help="Optional git base ref to compare against.")
    parser.add_argument("--check", action="store_true", help="Fail if pending candidates remain.")
    parser.add_argument("--quiet", action="store_true", help="Reduce output.")
    args = parser.parse_args()

    path = Path(".agent/rule-candidates.md")
    files = changed_files(args.base)
    statuses = existing_statuses(path)
    notes = existing_notes(path)
    candidates = all_candidates(files)
    path.write_text(render(candidates, statuses, notes), encoding="utf-8")

    pending = unresolved_count(path)
    if not args.quiet:
        print(f"Rule candidates: {len(candidates)} generated, {pending} pending.")
        print("Review .agent/rule-candidates.md and mark each candidate promoted, checked-unchanged, rejected, or needs-user.")
    if args.check and pending:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
