#!/usr/bin/env python3
"""Check whether current git changes may require shared agent-doc review.

This script maps changed files to .agent docs using .agent/drift-map.yml.
It does not decide that docs must be updated; it reports which docs should be
checked so users and agents do not have to guess.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path


def run_git(args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


# Kit-generated files must not create drift signals about themselves.
GENERATED_FILES = {
    ".agent/bootstrap-report.md",
    ".agent/project-map.md",
    ".agent/rule-candidates.md",
}
GENERATED_PREFIXES = (".agent/work/", ".rules-kit/")

# Vendor and build output must never produce drift signals, even when the
# repo has no .gitignore yet (mirrors bootstrap-project-context.py SKIP_DIRS).
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


def map_is_adapted() -> bool:
    try:
        text = Path(".agent/adaptation-review.md").read_text(encoding="utf-8")
    except OSError:
        return False
    return bool(re.search(r"^Status:\s*adapted\s*$", text, flags=re.MULTILINE))


def stale_globs(rules: list[dict[str, object]]) -> list[tuple[str, str]]:
    """Report concrete drift-map globs that no longer match any repo file.

    Only runs after adaptation (before that the map is a generic template and
    unmatched globs are expected), and only checks patterns anchored to a
    literal directory (e.g. `src/components/**`): a dead literal path means
    the map went stale — typically after a rename — and routing is silently
    blind there. The watcher needs a watcher.
    """
    if not map_is_adapted():
        return []
    repo_files = run_git(["ls-files"]) + run_git(["ls-files", "--others", "--exclude-standard"])
    stale: list[tuple[str, str]] = []
    for rule in rules:
        for pattern in rule.get("paths", []):  # type: ignore[union-attr]
            pattern = str(pattern)
            first_segment = pattern.split("/", 1)[0]
            if "/" not in pattern or any(ch in first_segment for ch in "*?["):
                continue
            if not any(matches(pattern, f) for f in repo_files):
                stale.append((str(rule.get("name", "unnamed")), pattern))
    return stale


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
            value = stripped[2:].strip().strip('"')
            current[active_list].append(value)  # type: ignore[index]

    if current:
        rules.append(current)

    return rules


def matches(pattern: str, file_path: str) -> bool:
    normalized = file_path.replace("\\", "/")
    pattern = pattern.replace("\\", "/")
    return fnmatch.fnmatch(normalized, pattern)


def main() -> int:
    parser = argparse.ArgumentParser(description="Report possible agent doc drift.")
    parser.add_argument("--base", help="Optional git base ref to compare against.")
    parser.add_argument("--map", default=".agent/drift-map.yml", help="Path to drift map.")
    parser.add_argument("--quiet", action="store_true", help="Only use exit status.")
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit 1 when drift candidates are found.",
    )
    args = parser.parse_args()

    files = changed_files(args.base)
    rules = parse_drift_map(Path(args.map))

    if not args.quiet:
        for rule_name, pattern in stale_globs(rules):
            print(
                f"Drift-map warning: [{rule_name}] glob `{pattern}` matches no tracked file — "
                "the map may be stale (renamed directory?). Update .agent/drift-map.yml and mirror .claude/rules/*.md."
            )

    if not files:
        if not args.quiet:
            print("Doc drift check: no changed files detected.")
        return 0

    hits: list[tuple[dict[str, object], list[str]]] = []
    for rule in rules:
        patterns = rule.get("paths", [])
        matched = [
            file_path
            for file_path in files
            if any(matches(str(pattern), file_path) for pattern in patterns)  # type: ignore[arg-type]
        ]
        if matched:
            hits.append((rule, matched))

    if not hits:
        if not args.quiet:
            print("Doc drift check: changed files did not match any drift-map rule.")
        return 0

    if not args.quiet:
        print("Doc drift check: review may be needed.")
        for rule, matched in hits:
            print(f"\n[{rule.get('name', 'unnamed')}] {rule.get('reason', '')}")
            print("Changed files:")
            for file_path in matched[:20]:
                print(f"  - {file_path}")
            if len(matched) > 20:
                print(f"  - ... {len(matched) - 20} more")
            print("Review docs:")
            for doc in rule.get("docs", []):  # type: ignore[assignment]
                print(f"  - {doc}")
        print("\nAgent expectation: say whether each suggested doc was updated, checked and unchanged, or out of scope.")

    return 1 if args.fail_on_drift else 0


if __name__ == "__main__":
    sys.exit(main())

