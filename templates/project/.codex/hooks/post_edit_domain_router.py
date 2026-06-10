#!/usr/bin/env python3
"""PostToolUse hook: on-demand domain-doc pointers for Codex.

Codex loads AGENTS.md once at startup and has no path-scoped rules, so this
hook fills that gap: after a file edit (apply_patch / Edit / Write), it maps
the touched paths against `.agent/drift-map.yml` and injects a one-line
pointer to the matching `.agent/domains/*` doc via `additionalContext`.

Claude Code does not need this hook; `.claude/rules/*.md` path-scoped rules
cover the same routing natively.

Noise control: each drift-map rule fires at most once per session (state is
kept in the system temp dir, keyed by session_id). On any unexpected payload
or error the hook stays silent and exits 0 — it is a router, not a gate.
"""

from __future__ import annotations

import fnmatch
import json
import re
import sys
import tempfile
from pathlib import Path


MAX_DOCS_PER_RULE = 2


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


def extract_strings(value: object) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, dict):
        for child in value.values():
            found.extend(extract_strings(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(extract_strings(child))
    return found


def candidate_paths(payload: dict) -> list[str]:
    cwd = str(payload.get("cwd") or "")
    paths: set[str] = set()
    for text in extract_strings(payload.get("tool_input")):
        # apply_patch carries paths inside patch markers.
        for match in re.findall(r"\*\*\* (?:Add|Update|Delete|Move to) File: (.+)", text):
            paths.add(match.strip())
        # Edit/Write carry plain path strings; keep only path-shaped values.
        if "\n" not in text and ("/" in text or re.search(r"\.[A-Za-z0-9]{1,12}$", text)):
            paths.add(text.strip())
    normalized: list[str] = []
    for path in paths:
        if cwd and path.startswith(cwd.rstrip("/") + "/"):
            path = path[len(cwd.rstrip("/")) + 1 :]
        normalized.append(path.lstrip("./"))
    return [path for path in normalized if path]


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
            current = {"name": line.split("name:", 1)[1].strip().strip('"'), "paths": [], "docs": []}
            active_list = None
            continue
        if current is None:
            continue
        stripped = line.strip()
        if stripped in {"paths:", "docs:"}:
            active_list = stripped[:-1]
            continue
        if stripped.startswith("reason:"):
            active_list = None
            continue
        if stripped.startswith("- ") and active_list in {"paths", "docs"}:
            current[active_list].append(stripped[2:].strip().strip('"'))  # type: ignore[union-attr]
    if current:
        rules.append(current)
    return rules


def seen_state_path(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id)[:80] or "default"
    return Path(tempfile.gettempdir()) / f"rules-domain-router-{safe}.json"


def load_seen(path: Path) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {item for item in data if isinstance(item, str)} if isinstance(data, list) else set()


def save_seen(path: Path, seen: set[str]) -> None:
    try:
        path.write_text(json.dumps(sorted(seen)), encoding="utf-8")
    except OSError:
        pass


def main() -> int:
    payload = stdin_payload()
    paths = candidate_paths(payload)
    if not paths:
        return 0

    rules = parse_drift_map(Path(".agent/drift-map.yml"))
    if not rules:
        return 0

    state = seen_state_path(str(payload.get("session_id") or "default"))
    seen = load_seen(state)

    pointers: list[str] = []
    for rule in rules:
        name = str(rule.get("name", ""))
        if not name or name in seen:
            continue
        patterns = [str(p) for p in rule.get("paths", [])]  # type: ignore[arg-type]
        if not any(fnmatch.fnmatch(path, pattern) for path in paths for pattern in patterns):
            continue
        seen.add(name)
        docs = [str(d) for d in rule.get("docs", [])][:MAX_DOCS_PER_RULE]  # type: ignore[arg-type]
        if docs:
            pointers.append(f"{name}: read {' and '.join(f'`{doc}`' for doc in docs)}")

    if not pointers:
        return 0

    save_seen(state, seen)
    context = "Rules router: your edit touched mapped areas — " + "; ".join(pointers) + ". Verify doc claims against current code."
    print(json.dumps({"additionalContext": context}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
