#!/usr/bin/env python3
"""Generate rule-maintenance candidates from current project evidence.

The script writes candidates to .agent/rule-candidates.md. It never promotes
candidates into official rules. Agents must inspect evidence and mark each item
promoted, checked-unchanged, rejected, or needs-user before finalizing work.

Persistence model:
- A candidate's identity is `<id>@<evidence-key>`, where the key hashes the
  evidence set. New evidence for the same rule resets the candidate to pending
  instead of silently inheriting an old decision.
- Pending candidates are never dropped by regeneration. If their files leave
  the diff they are carried forward verbatim until an agent resolves them.
- Resolved candidates move to a compact archive section that preserves the
  decision trail, and a resolved status keyed to the same evidence suppresses
  re-emission, so rejected items do not come back as zombies.
- Resolving a candidate requires a real decision note: a status flipped to
  resolved while the notes still say `- pending` reverts to pending.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_STATUSES = {"pending", "promoted", "checked-unchanged", "rejected", "needs-user"}

# Kit-generated files must not create candidates about themselves.
GENERATED_FILES = {
    ".agent/bootstrap-report.md",
    ".agent/project-map.md",
    ".agent/rule-candidates.md",
}
GENERATED_PREFIXES = (".agent/work/", ".rules-kit/")

# Vendor and build output must never produce candidates, even when the repo
# has no .gitignore yet (mirrors bootstrap-project-context.py SKIP_DIRS).
VENDOR_SEGMENTS = {
    "node_modules",
    "DerivedData",
    "build",
    "dist",
    ".next",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "coverage",
    ".turbo",
    "Pods",
}

ARCHIVE_BEGIN = "# BEGIN RESOLVED CANDIDATE ARCHIVE"
ARCHIVE_END = "# END RESOLVED CANDIDATE ARCHIVE"
GENERATED_BEGIN = "# BEGIN GENERATED RULE CANDIDATES"
GENERATED_END = "# END GENERATED RULE CANDIDATES"
MAX_ARCHIVE = 30

# A candidate id always starts with one of these. Only `### <id>` headings with
# a known prefix, inside the generated block, are candidates — so a Markdown
# heading a human writes in a decision note (e.g. `### TODO`) is never parsed as
# a phantom candidate.
KNOWN_PREFIXES = ("drift:", "command:", "backup:", "risk:")


def is_candidate_id(value: str) -> bool:
    return value.startswith(KNOWN_PREFIXES)

# Fallback when .agent/rules-kit.json predates the managedPaths field.
DEFAULT_MANAGED_PATHS = [
    "AGENTS.md",
    "CLAUDE.md",
    ".agent",
    ".agents",
    ".claude",
    ".codex",
    "scripts/check-doc-drift.py",
    "scripts/bootstrap-project-context.py",
    "scripts/suggest-rule-updates.py",
]


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


def is_vendor(file_path: str) -> bool:
    return any(segment in VENDOR_SEGMENTS for segment in file_path.split("/"))


def changed_files(base: str | None) -> list[str]:
    files: set[str] = set()
    # --no-renames keeps the old path visible when a mapped directory is
    # renamed away, so the move fires its old drift rule one last time.
    if base:
        files.update(run_git(["diff", "--no-renames", "--name-only", base, "--"]))
    else:
        files.update(run_git(["diff", "--no-renames", "--name-only", "--"]))
        files.update(run_git(["diff", "--no-renames", "--cached", "--name-only", "--"]))
    files.update(run_git(["ls-files", "--others", "--exclude-standard"]))
    kept = [
        f
        for f in files
        if f not in GENERATED_FILES
        and not any(f.startswith(p) for p in GENERATED_PREFIXES)
        and not is_vendor(f)
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


def evidence_key(evidence: list[str]) -> str:
    digest = hashlib.sha1("\n".join(sorted(evidence)).encode("utf-8")).hexdigest()
    return digest[:7]


ID_PATTERN = re.compile(r"^###\s+([A-Za-z0-9_.:@+-]+)\s*$")
ARCHIVE_LINE = re.compile(
    r"^-\s+(?P<id>[A-Za-z0-9_.:@+-]+)\s+\|\s+(?P<status>[a-z-]+)\s+\|\s+(?P<date>\S+)\s+\|\s+(?P<key>\S*)\s+\|\s+(?P<note>.*)$"
)


def parse_blocks(path: Path) -> dict[str, dict[str, object]]:
    """Parse candidate blocks from the generated section only.

    Headers are recognized only inside the generated block and only when the id
    has a known candidate prefix, so a `### ...` heading written inside a human
    decision note is never mistaken for a new candidate.
    """
    blocks: dict[str, dict[str, object]] = {}
    text = read_text(path)
    current_id: str | None = None
    raw_lines: list[str] = []
    in_generated = False

    def flush() -> None:
        nonlocal current_id, raw_lines
        if current_id is None:
            return
        status = "pending"
        evidence_key = ""
        notes: list[str] = []
        in_notes = False
        for line in raw_lines:
            status_match = re.match(r"^Status:\s*([A-Za-z-]+)\s*$", line.strip())
            if status_match and status_match.group(1) in ALLOWED_STATUSES:
                status = status_match.group(1)
            key_match = re.match(r"^EvidenceKey:\s*(\S+)\s*$", line.strip())
            if key_match:
                evidence_key = key_match.group(1)
            if line.strip() == "Decision notes:":
                in_notes = True
                continue
            if in_notes:
                if line.strip() == "":
                    in_notes = False
                else:
                    notes.append(line)
        blocks[current_id] = {
            "status": status,
            "notes": notes,
            "raw": list(raw_lines),
            "evidence_key": evidence_key,
        }
        current_id = None
        raw_lines = []

    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped == GENERATED_BEGIN:
            in_generated = True
            continue
        if stripped == GENERATED_END:
            flush()
            in_generated = False
            continue
        if not in_generated:
            continue
        id_match = ID_PATTERN.match(stripped)
        if id_match and is_candidate_id(id_match.group(1)):
            flush()
            current_id = id_match.group(1)
            raw_lines = [raw]
            continue
        if current_id is not None:
            raw_lines.append(raw)
    flush()
    return blocks


def parse_archive(path: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    in_archive = False
    for raw in read_text(path).splitlines():
        if raw.strip() == ARCHIVE_BEGIN:
            in_archive = True
            continue
        if raw.strip() == ARCHIVE_END:
            break
        if not in_archive:
            continue
        line_match = ARCHIVE_LINE.match(raw.strip())
        if line_match and line_match.group("status") in ALLOWED_STATUSES:
            entries.append(
                {
                    "id": line_match.group("id"),
                    "status": line_match.group("status"),
                    "date": line_match.group("date"),
                    "key": line_match.group("key"),
                    "note": line_match.group("note").strip(),
                }
            )
    return entries


def existing_timestamp(path: Path) -> str | None:
    for raw in read_text(path).splitlines():
        ts_match = re.match(r"^Generated:\s*(\S+)\s*$", raw.strip())
        if ts_match:
            return ts_match.group(1)
    return None


def meaningful_notes(notes: list[str]) -> bool:
    joined = " ".join(line.strip().lstrip("-").strip() for line in notes).strip()
    return len(joined) >= 10 and joined.lower() != "pending"


def drift_candidates(files: list[str]) -> list[dict[str, object]]:
    raw: list[dict[str, object]] = []
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
        raw.append(
            {
                "names": [slugify(str(rule.get("name", "unnamed")))],
                "evidence": matched[:20],
                "docs": [str(doc) for doc in rule.get("docs", [])],  # type: ignore[arg-type]
                "reasons": [str(rule.get("reason", ""))],
            }
        )

    # Merge rules that fired on the identical file set: one change, one
    # candidate, one review — overlapping globs must not double the inbox.
    merged: dict[tuple[str, ...], dict[str, object]] = {}
    for item in raw:
        key = tuple(item["evidence"])  # type: ignore[arg-type]
        if key in merged:
            merged[key]["names"].extend(item["names"])  # type: ignore[union-attr]
            for doc in item["docs"]:  # type: ignore[union-attr]
                if doc not in merged[key]["docs"]:  # type: ignore[operator]
                    merged[key]["docs"].append(doc)  # type: ignore[union-attr]
            merged[key]["reasons"].extend(item["reasons"])  # type: ignore[union-attr]
        else:
            merged[key] = item

    candidates: list[dict[str, object]] = []
    for item in merged.values():
        names = sorted(set(item["names"]))  # type: ignore[arg-type]
        evidence = list(item["evidence"])  # type: ignore[arg-type]
        # Edits that touch only .agent/* docs are rule maintenance, not code
        # drift; auto-classify so promotions do not spawn an endless second
        # round of review-the-review.
        doc_only = all(str(f).startswith(".agent/") for f in evidence)
        candidates.append(
            {
                "id": "drift:" + "+".join(names),
                "title": f"Review rule docs for changed {', '.join(names)} paths",
                "kind": "drift",
                "default_status": "checked-unchanged" if doc_only else "pending",
                "auto_note": "rule-doc maintenance edit; auto-classified by scanner" if doc_only else "",
                "evidence": evidence,
                "docs": item["docs"],
                "action": "Agent should inspect changed files and decide whether to update, keep unchanged, or reject rule changes.",
                "reason": "; ".join(r for r in item["reasons"] if r),  # type: ignore[union-attr]
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
                "auto_note": "",
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
        # A backup identical to the live file is a previous kit install or an
        # unmodified template — nothing to mine, so no candidate.
        if text == read_text(Path(path.name), limit=80_000):
            continue
        headings = [line.strip() for line in text.splitlines() if line.startswith("#")][:20]
        candidates.append(
            {
                "id": f"backup:{slugify(str(path))}",
                "title": f"Review old rule backup `{path.as_posix()}`",
                "kind": "backup",
                "default_status": "pending",
                "auto_note": "",
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
                "auto_note": "",
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
            # The id is stable per rule (e.g. `risk:billing`). The evidence
            # fingerprint is a field, not part of the id, so a rule fires ONE
            # candidate no matter how many files it matches over a task.
            candidate["key"] = evidence_key([str(e) for e in candidate["evidence"]])  # type: ignore[arg-type]
            candidate["full_id"] = str(candidate["id"])
            fid = str(candidate["full_id"])
            if fid in seen:
                continue
            seen.add(fid)
            candidates.append(candidate)
    return candidates


def managed_paths() -> list[str]:
    meta = Path(".agent/rules-kit.json")
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
        paths = data.get("managedPaths")
        if isinstance(paths, list) and paths:
            return [str(p) for p in paths]
    except (OSError, json.JSONDecodeError):
        pass
    return DEFAULT_MANAGED_PATHS


def is_managed(file_path: str, managed: list[str]) -> bool:
    return any(file_path == m or file_path.startswith(m.rstrip("/") + "/") for m in managed)


def render_block(candidate: dict[str, object], status: str, notes: list[str]) -> list[str]:
    lines = [
        f"### {candidate['full_id']}",
        f"Status: {status}",
        f"Kind: {candidate.get('kind', 'unknown')}",
        f"EvidenceKey: {candidate.get('key', '')}",
        f"Title: {candidate.get('title', '')}",
        f"Reason: {candidate.get('reason', '')}",
        "Evidence:",
    ]
    for item in candidate.get("evidence", []):  # type: ignore[assignment]
        lines.append(f"- `{item}`")
    lines.append("Review docs:")
    for doc in candidate.get("docs", []):  # type: ignore[assignment]
        lines.append(f"- `{doc}`")
    lines.extend([f"Agent action: {candidate.get('action', '')}", "Decision notes:"])
    if notes and meaningful_notes(notes):
        lines.extend(notes)
    else:
        lines.append("- pending")
    lines.append("")
    return lines


HEADER = [
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
    "- `pending`: not yet handled. Pending high-risk (`risk:*`) candidates block finalization; drift and command candidates are advisory and do not block.",
    "",
    "A decision requires a real note: statuses flipped without decision notes revert to pending on the next scan. Resolved items move to the archive section below and stay resolved.",
    "",
    "Agent rule: decide autonomously whenever current evidence is enough. Do not ask the user to classify ordinary candidates.",
    "",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or validate rule update candidates.")
    parser.add_argument("--base", help="Optional git base ref to compare against.")
    parser.add_argument("--check", action="store_true", help="Fail if pending candidates remain.")
    parser.add_argument(
        "--gate",
        action="store_true",
        help="With --check, fail only on pending high-risk (risk:*) candidates; advisory drift/command candidates do not fail.",
    )
    parser.add_argument("--quiet", action="store_true", help="Reduce output.")
    parser.add_argument(
        "--resolve-kit-install",
        action="store_true",
        help="Auto-resolve candidates whose evidence is only kit-installed files (used by the installer).",
    )
    args = parser.parse_args()

    path = Path(".agent/rule-candidates.md")
    files = changed_files(args.base)
    blocks = parse_blocks(path)
    archive = parse_archive(path)
    candidates = all_candidates(files)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archived_status = {entry["id"]: entry for entry in archive}
    managed = managed_paths() if args.resolve_kit_install else []

    pending_sections: list[list[str]] = []
    new_archive: list[dict[str, str]] = []
    generated_ids: set[str] = set()
    pending_risk = 0  # high-stakes candidates that gate the Stop hook

    for candidate in candidates:
        fid = str(candidate["full_id"])
        cur_key = str(candidate.get("key", ""))
        generated_ids.add(fid)
        prev = blocks.get(fid)
        status = str(candidate.get("default_status", "pending"))
        notes: list[str] = []
        auto_note = str(candidate.get("auto_note", ""))
        if prev:
            status = str(prev["status"])
            notes = list(prev["notes"])  # type: ignore[arg-type]
            # Reopen a resolved candidate only when the rule fired on genuinely
            # new evidence (fingerprint changed), not on every scan.
            if status != "pending" and prev.get("evidence_key") and prev["evidence_key"] != cur_key:
                status = "pending"
                notes = []
        elif fid in archived_status:
            entry = archived_status[fid]
            if entry.get("key") and entry["key"] != cur_key:
                status = "pending"
                notes = []
            else:
                status = entry["status"]
                notes = [f"- {entry['note']}"] if entry["note"] else []
        if (
            args.resolve_kit_install
            and status == "pending"
            and candidate.get("kind") in {"drift", "risk"}
            and all(is_managed(str(e), managed) for e in candidate["evidence"])  # type: ignore[arg-type]
        ):
            status = "checked-unchanged"
            notes = ["- kit installation files; auto-resolved by installer"]
        if status not in ALLOWED_STATUSES:
            status = "pending"
        # Anti-rubber-stamp: a resolved status without a real decision note
        # is not a decision. Auto-classified items carry their own note.
        if status != "pending" and not meaningful_notes(notes):
            if auto_note:
                notes = [f"- {auto_note}"]
            else:
                status = "pending"
        if status == "pending":
            pending_sections.append(render_block(candidate, status, notes))
            if candidate.get("kind") == "risk":
                pending_risk += 1
        else:
            first_note = next((line.strip().lstrip("-").strip() for line in notes if line.strip()), "")
            new_archive.append({"id": fid, "status": status, "date": today, "key": cur_key, "note": first_note})

    def carry(raw: list[str]) -> list[str]:
        # Strip trailing blank lines, then append exactly one separator, so a
        # carried block is byte-stable across no-op re-runs (no growing diff).
        trimmed = list(raw)
        while trimmed and not trimmed[-1].strip():
            trimmed.pop()
        return trimmed + [""]

    # Carry forward previously pending candidates whose files left the diff;
    # they stay in the inbox until an agent resolves them.
    carried = 0
    for fid, block in blocks.items():
        if fid in generated_ids:
            continue
        if block["status"] == "pending":
            pending_sections.append(carry(block["raw"]))  # type: ignore[arg-type]
            carried += 1
            if fid.startswith("risk:") or any(
                line.strip() == "Kind: risk" for line in block["raw"]  # type: ignore[union-attr]
            ):
                pending_risk += 1
        else:
            notes = list(block["notes"])  # type: ignore[arg-type]
            if not meaningful_notes(notes):
                # Resolved without a note and no longer reproducible from the
                # diff: keep it in the inbox rather than blessing the flip.
                pending_sections.append(
                    carry([re.sub(r"^Status:.*$", "Status: pending", line) for line in block["raw"]])
                )
                carried += 1
                if fid.startswith("risk:") or any(
                    line.strip() == "Kind: risk" for line in block["raw"]  # type: ignore[union-attr]
                ):
                    pending_risk += 1
                continue
            first_note = next((line.strip().lstrip("-").strip() for line in notes if line.strip()), "")
            new_archive.append(
                {
                    "id": fid,
                    "status": str(block["status"]),
                    "date": today,
                    "key": str(block.get("evidence_key", "")),
                    "note": first_note,
                }
            )

    # Merge archives: newly resolved first, then prior entries, dedupe by id.
    seen_archive: set[str] = set()
    merged_archive: list[dict[str, str]] = []
    for entry in new_archive + archive:
        if entry["id"] in seen_archive:
            continue
        seen_archive.add(entry["id"])
        merged_archive.append(entry)
    merged_archive = merged_archive[:MAX_ARCHIVE]

    pending = len(pending_sections)

    body: list[str] = []
    body.append(GENERATED_BEGIN)
    body.append("Generated: {timestamp}")
    body.append("")
    if not pending_sections:
        body.append("- no current candidates")
        body.append("")
    for section in pending_sections:
        body.extend(section)
    body.append(GENERATED_END)
    body.append("")
    body.append(ARCHIVE_BEGIN)
    if not merged_archive:
        body.append("- no resolved candidates yet")
    for entry in merged_archive:
        body.append(
            f"- {entry['id']} | {entry['status']} | {entry['date']} | {entry.get('key', '')} | {entry['note']}"
        )
    body.append(ARCHIVE_END)

    content_template = "\n".join(HEADER + body).rstrip() + "\n"

    # Only touch the file when the content (minus the timestamp) actually
    # changed: checks and Stop-hook runs must not churn a tracked file.
    old_text = read_text(path)
    old_ts = existing_timestamp(path)
    if old_ts and content_template.replace("{timestamp}", old_ts) == old_text:
        final_text = old_text
    else:
        final_text = content_template.replace(
            "{timestamp}", datetime.now(timezone.utc).isoformat(timespec="seconds")
        )
        path.write_text(final_text, encoding="utf-8")

    if not args.quiet:
        risk_note = f" ({pending_risk} high-risk)" if pending_risk else ""
        print(
            f"Rule candidates: {len(candidates)} generated, {carried} carried forward, "
            f"{pending} pending{risk_note}, {len(merged_archive)} archived."
        )
        if pending:
            print("Review .agent/rule-candidates.md and mark each candidate promoted, checked-unchanged, rejected, or needs-user.")
    if args.check:
        if args.gate:
            # Stop-gate scope: only high-stakes candidates block.
            return 1 if pending_risk else 0
        return 1 if pending else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
