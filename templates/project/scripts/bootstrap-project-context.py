#!/usr/bin/env python3
"""Bootstrap project-specific agent context from current repository evidence.

This script intentionally writes conservative, reviewable context:
- project-map.md: facts detectable from files/config
- command-contract.md: generated command candidates only; verified inventory is preserved
- bootstrap-report.md: evidence, old-rule clues, and review TODOs
- rule-candidates.md: generated maintenance inbox for agent decisions

It does not claim live device, release, remote, billing, or production state.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".rules-kit",
    ".agent",
    ".agents",
    ".claude",
    ".codex",
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

GENERATED_PROJECT_PATHS_BEGIN = "# BEGIN GENERATED PROJECT PATHS"
GENERATED_PROJECT_PATHS_END = "# END GENERATED PROJECT PATHS"

PROJECT_DRIFT_MAPPINGS = {
    "ui": (
        "project-ui",
        [".agent/domains/ui-copy.md", ".agent/user-journeys.md", ".agent/quality-gates.md"],
        "Project-specific UI paths detected by bootstrap.",
    ),
    "models": (
        "project-data-models",
        [".agent/domains/data-sync.md", ".agent/quality-gates.md"],
        "Project-specific model/schema paths detected by bootstrap.",
    ),
    "services": (
        "project-services",
        [".agent/domains/data-sync.md", ".agent/tool-policy.md", ".agent/quality-gates.md"],
        "Project-specific service/api/client/sync/backup/import/export paths detected by bootstrap.",
    ),
    "tests": (
        "project-tests",
        [".agent/domains/build-test.md", ".agent/command-contract.md", ".agent/verification-map.md"],
        "Project-specific test paths detected by bootstrap.",
    ),
    "release": (
        "project-release",
        [".agent/domains/release.md", ".agent/workflows/release.md", ".agent/tool-policy.md"],
        "Project-specific release/deploy/signing paths detected by bootstrap.",
    ),
    "localization": (
        "project-localization",
        [".agent/domains/localization.md", ".agent/domains/ui-copy.md"],
        "Project-specific localization paths detected by bootstrap.",
    ),
}


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def find_files(root: Path, max_depth: int = 5) -> list[Path]:
    files: list[Path] = []
    for current, dirs, filenames in os.walk(root):
        current_path = Path(current)
        depth = len(current_path.relative_to(root).parts)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and depth < max_depth]
        for filename in filenames:
            files.append(current_path / filename)
    return files


def read_text(path: Path, limit: int = 200_000) -> str:
    try:
        data = path.read_bytes()[:limit]
        return data.decode("utf-8", errors="replace")
    except OSError:
        return ""


def run_git(root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def detect_project(root: Path, files: list[Path]) -> dict[str, object]:
    rels = {rel(path, root) for path in files}
    dirs = {part for path in files for part in path.relative_to(root).parts[:-1]}
    detected: list[str] = []

    markers = {
        "ios-xcodegen": "project.yml",
        "swift-package": "Package.swift",
        "node": "package.json",
        "python": "pyproject.toml",
        "ruby": "Gemfile",
        "fastlane": "fastlane/Fastfile",
        "github-actions": ".github/workflows",
    }
    for name, marker in markers.items():
        if marker in rels or marker in dirs:
            detected.append(name)

    lproj = sorted({path.parent.name for path in files if path.parent.name.endswith(".lproj")})
    locales = sorted(
        {
            path.parent.name
            for path in files
            if any(part in {"locales", "locale", "i18n", "translations"} for part in path.parts)
        }
    )

    return {
        "detected": detected,
        "lproj": lproj,
        "locales": locales,
    }


def parse_package_json(root: Path) -> list[tuple[str, str]]:
    path = root / "package.json"
    if not path.exists():
        return []
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError:
        return []
    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return []
    return [(name, f"npm run {name}") for name in sorted(scripts)]


def parse_project_yml(root: Path) -> list[tuple[str, str]]:
    path = root / "project.yml"
    if not path.exists():
        return []
    text = read_text(path)
    schemes: list[str] = []
    in_schemes = False
    for line in text.splitlines():
        if re.match(r"^schemes:\s*$", line):
            in_schemes = True
            continue
        if in_schemes and line and not line.startswith((" ", "\t")):
            in_schemes = False
        if in_schemes:
            match = re.match(r"^\s{2}([A-Za-z0-9_. -]+):\s*$", line)
            if match:
                schemes.append(match.group(1).strip())
    if not schemes:
        name_match = re.search(r"^name:\s*([A-Za-z0-9_. -]+)\s*$", text, re.MULTILINE)
        if name_match:
            schemes.append(name_match.group(1).strip())
    commands: list[tuple[str, str]] = []
    for scheme in sorted(set(schemes)):
        project_arg = "<ProjectName>.xcodeproj"
        commands.append((f"build:{scheme}", f"xcodebuild -project {project_arg} -scheme {scheme} build"))
        commands.append((f"test:{scheme}", f"xcodebuild -project {project_arg} -scheme {scheme} test"))
    if path.exists():
        commands.insert(0, ("generate:xcodegen", "xcodegen generate"))
    return commands


def command_candidates(root: Path) -> list[tuple[str, str, str]]:
    candidates: list[tuple[str, str, str]] = []
    for name, command in parse_package_json(root):
        purpose = {
            "test": "Unit tests",
            "lint": "Lint",
            "typecheck": "Typecheck",
            "build": "Build",
            "format": "Format",
        }.get(name, f"Script: {name}")
        candidates.append((purpose, command, "Detected from package.json scripts. Verify before relying on it."))
    for name, command in parse_project_yml(root):
        purpose = "Build/Test" if name.startswith(("build:", "test:")) else "Generate"
        candidates.append((purpose, command, "Detected from project.yml. Destination/project details may need adjustment."))
    if (root / "Makefile").exists():
        candidates.append(("Make", "make <target>", "Makefile detected. Inspect targets before use."))
    if (root / "justfile").exists():
        candidates.append(("Just", "just <recipe>", "justfile detected. Inspect recipes before use."))
    if (root / "pyproject.toml").exists():
        candidates.append(("Python tests", "python -m pytest", "pyproject.toml detected. Verify test runner."))
    return candidates


def segmentize(path: str) -> str:
    """Lowercase a path with camelCase boundaries turned into separators.

    Keep in sync with scripts/suggest-rule-updates.py. Word-boundary matching
    on segmentized paths keeps "Product" from matching "prod" and
    "importHelpers" from matching a data-import signal by accident.
    """
    split_camel = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", path)
    split_acronym = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "-", split_camel)
    return split_acronym.lower()


_B = r"(^|[-_./])"
_E = r"([-_./]|$)"


def classify_paths(root: Path, files: list[Path]) -> dict[str, list[str]]:
    rels = [rel(path, root) for path in files]

    def pick(patterns: tuple[str, ...], limit: int = 20) -> list[str]:
        matches: list[str] = []
        for item in rels:
            segmented = segmentize(item)
            if any(re.search(pattern, segmented) for pattern in patterns):
                matches.append(item)
        return sorted(matches)[:limit]

    return {
        "ui": pick((r"/views?/", r"/components?/", r"/screens?/", r"/pages/", r"/layouts/", rf"{_B}view\.", rf"{_B}screen\.")),
        "models": pick((r"/models?/", r"/schemas?/", rf"{_B}schema{_E}", rf"{_B}migrations?{_E}")),
        "services": pick((rf"{_B}services?{_E}", rf"{_B}api{_E}", rf"{_B}clients?{_E}", rf"{_B}sync{_E}", rf"{_B}backups?{_E}", rf"{_B}(import|export)(er|ers)?{_E}")),
        "tests": pick((r"/tests?/", r"/__tests__/", rf"{_B}tests?\.", rf"{_B}spec\.", r"\.test\.", r"\.spec\.")),
        "release": pick((rf"{_B}fastlane{_E}", rf"{_B}export-?options", r"\.entitlements$", r"\.github/workflows", rf"{_B}releases?{_E}", rf"{_B}deploy(ment)?s?{_E}", rf"{_B}signing{_E}")),
        "localization": pick((r"\.lproj/", r"/locales?/", r"/i18n/", r"/translations/", r"\.strings$", r"\.stringsdict$", r"\.xcstrings$", r"\.xliff$", r"\.arb$", r"\.po$")),
    }


def old_rule_clues(root: Path) -> list[str]:
    clues: list[str] = []
    backup_root = root / ".rules-kit" / "backups"
    if not backup_root.exists():
        return clues
    for path in sorted(backup_root.glob("rules-install-*/*")):
        if path.name not in {"AGENTS.md", "CLAUDE.md"}:
            continue
        text = read_text(path, limit=80_000)
        headings = [line.strip() for line in text.splitlines() if line.startswith("#")][:20]
        clues.append(f"Backup `{rel(path, root)}` contains headings: {', '.join(headings) if headings else 'no markdown headings found'}")
    return clues


def write_project_map(root: Path, project: dict[str, object], paths: dict[str, list[str]], commands: list[tuple[str, str, str]]) -> None:
    lines: list[str] = [
        "# Project Map",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "This file is generated from current files/config. Treat it as a map, not proof of product intent.",
        "",
        "## Detected Project Types",
        "",
    ]
    detected = project.get("detected") or []
    if detected:
        lines.extend(f"- {item}" for item in detected)  # type: ignore[union-attr]
    else:
        lines.append("- none detected")

    lines.extend(["", "## Localization Signals", ""])
    lproj = project.get("lproj") or []
    locales = project.get("locales") or []
    if lproj:
        lines.append(f"- lproj directories: {', '.join(lproj)}")  # type: ignore[arg-type]
    if locales:
        lines.append(f"- locale directories: {', '.join(locales)}")  # type: ignore[arg-type]
    if not lproj and not locales:
        lines.append("- none detected")

    lines.extend(["", "## Path Signals", ""])
    for key, values in paths.items():
        lines.append(f"### {key}")
        if values:
            lines.extend(f"- `{value}`" for value in values)
        else:
            lines.append("- none detected")
        lines.append("")

    lines.extend(["## Command Candidates", ""])
    if commands:
        for purpose, command, note in commands:
            lines.append(f"- **{purpose}**: `{command}`")
            lines.append(f"  Evidence: {note}")
    else:
        lines.append("- none detected")

    (root / ".agent" / "project-map.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def default_command_contract() -> str:
    lines = [
        "# Command Contract",
        "",
        "Commands in project docs are examples until verified in the current repo.",
        "",
        "This file gives agents a single place to discover and update the project's current validation commands.",
        "",
        "## Command Inventory",
        "",
        "Fill or edit this section after installing the rules kit in a real project. This section is human/agent maintained; bootstrap does not overwrite it.",
        "",
        "| Purpose | Command | Evidence Expected | Notes |",
        "|---|---|---|---|",
        "| Format | project-specific | exits 0 | optional |",
        "| Lint | project-specific | exits 0 | optional |",
        "| Typecheck | project-specific | exits 0 | optional |",
        "| Unit tests | project-specific | exits 0 | targeted first |",
        "| Build | project-specific | exits 0 | required before release |",
        "| UI/runtime smoke | project-specific | visible path works | use browser/device when relevant |",
        "| Release verification | project-specific | live tool confirms state | explicit high-risk workflow |",
        "",
        "## Auto-Detected Command Candidates",
        "",
        "Bootstrap refreshes only the block below. Promote a candidate into Command Inventory after verifying it.",
        "",
        "# BEGIN GENERATED COMMAND CANDIDATES",
        "- none detected",
        "# END GENERATED COMMAND CANDIDATES",
        "",
        "## Rules",
        "",
        "- Before running a documented command for the first time in a task, verify it still exists.",
        "- Prefer the smallest command that proves the affected behavior.",
        "- If a command is missing or stale, inspect scripts/config to find the current one and update this file when the command is durable.",
        "- Do not claim validation passed without current command output or tool evidence.",
        "- For slow or unavailable commands, run the safest targeted alternative and state the remaining risk.",
    ]
    return "\n".join(lines) + "\n"


def generated_command_block(commands: list[tuple[str, str, str]]) -> str:
    lines = [
        "# BEGIN GENERATED COMMAND CANDIDATES",
        "# Generated by scripts/bootstrap-project-context.py.",
        "# Review these candidates; they are not verified command contracts.",
    ]
    if commands:
        lines.extend(
            [
                "",
                "| Purpose | Command | Evidence |",
                "|---|---|---|",
            ]
        )
        for purpose, command, note in commands:
            safe_command = command.replace("|", "\\|")
            safe_note = note.replace("|", "\\|")
            lines.append(f"| {purpose} | `{safe_command}` | {safe_note} |")
    else:
        lines.append("- none detected")
    lines.append("# END GENERATED COMMAND CANDIDATES")
    return "\n".join(lines)


def write_command_contract(root: Path, commands: list[tuple[str, str, str]]) -> None:
    contract_path = root / ".agent" / "command-contract.md"
    text = read_text(contract_path) if contract_path.exists() else default_command_contract()
    block = generated_command_block(commands)
    pattern = re.compile(
        r"\n?# BEGIN GENERATED COMMAND CANDIDATES\n.*?# END GENERATED COMMAND CANDIDATES\n?",
        re.DOTALL,
    )
    if pattern.search(text):
        new_text = pattern.sub("\n" + block + "\n", text)
    else:
        insert_after = "## Auto-Detected Command Candidates\n"
        candidate_intro = (
            "## Auto-Detected Command Candidates\n\n"
            "Bootstrap refreshes only the block below. Promote a candidate into Command Inventory after verifying it.\n\n"
            f"{block}\n"
        )
        if insert_after in text:
            new_text = text.replace(insert_after, candidate_intro, 1)
        elif "## Rules\n" in text:
            new_text = text.replace("## Rules\n", candidate_intro + "\n## Rules\n", 1)
        else:
            new_text = text.rstrip() + "\n\n" + candidate_intro
    contract_path.write_text(new_text.rstrip() + "\n", encoding="utf-8")


def top_dirs(values: list[str], max_items: int = 8) -> list[str]:
    dirs: list[str] = []
    for value in values:
        parts = Path(value).parts
        if not parts:
            continue
        # Values are file paths, so the directory is always everything but the
        # last component. (Using suffix to decide turned extension-less files
        # like Dockerfile/Makefile into dead `Dockerfile/**` globs.)
        parent_parts = parts[:-1]
        if len(parent_parts) >= 2:
            candidate = f"{parent_parts[0]}/{parent_parts[1]}/**"
        elif len(parent_parts) == 1:
            candidate = f"{parent_parts[0]}/**"
        elif len(parts) == 1:
            candidate = parts[0]
        else:
            continue
        if candidate not in dirs:
            dirs.append(candidate)
    return dirs[:max_items]


def project_drift_rules(paths: dict[str, list[str]]) -> list[dict[str, object]]:
    rules: list[dict[str, object]] = []
    for key, (name, docs, reason) in PROJECT_DRIFT_MAPPINGS.items():
        candidates = top_dirs(paths.get(key, []))
        if candidates:
            rules.append({"name": name, "paths": candidates, "docs": docs, "reason": reason})
    return rules


def generated_drift_block(paths: dict[str, list[str]]) -> str:
    rules = project_drift_rules(paths)

    lines = [
        "# BEGIN GENERATED PROJECT DRIFT CANDIDATES",
        "# Generated by scripts/bootstrap-project-context.py.",
        "# Review these candidates; they are path signals, not proof docs must change.",
    ]
    for rule in rules:
        lines.extend(
            [
                f"  - name: {rule['name']}",
                "    paths:",
            ]
        )
        lines.extend(f'      - "{candidate}"' for candidate in rule["paths"])  # type: ignore[union-attr]
        lines.append("    docs:")
        lines.extend(f'      - "{doc}"' for doc in rule["docs"])  # type: ignore[union-attr]
        lines.append(f'    reason: "{rule["reason"]}"')
        lines.append("")
    if not rules:
        lines.append("  # No project-specific candidates detected yet.")
    lines.append("# END GENERATED PROJECT DRIFT CANDIDATES")
    return "\n".join(lines).rstrip()


def is_adapted(root: Path) -> bool:
    try:
        text = (root / ".agent" / "adaptation-review.md").read_text(encoding="utf-8")
    except OSError:
        return False
    return bool(re.search(r"^Status:\s*adapted\s*$", text, flags=re.MULTILINE))


def domain_pointer_name(doc: str) -> str | None:
    prefix = ".agent/domains/"
    suffix = ".md"
    if doc.startswith(prefix) and doc.endswith(suffix):
        return doc[len(prefix) : -len(suffix)]
    return None


def generated_paths_by_pointer(rules: list[dict[str, object]]) -> dict[str, list[str]]:
    by_pointer: dict[str, list[str]] = {}
    for rule in rules:
        paths = [str(path) for path in rule.get("paths", [])]  # type: ignore[arg-type]
        for doc in rule.get("docs", []):  # type: ignore[assignment]
            pointer = domain_pointer_name(str(doc))
            if not pointer:
                continue
            bucket = by_pointer.setdefault(pointer, [])
            for path in paths:
                if path not in bucket:
                    bucket.append(path)
    return by_pointer


def strip_generated_project_paths(lines: list[str]) -> list[str]:
    kept: list[str] = []
    in_generated = False
    for line in lines:
        marker = line.strip()
        if marker == GENERATED_PROJECT_PATHS_BEGIN:
            in_generated = True
            continue
        if in_generated:
            if marker == GENERATED_PROJECT_PATHS_END:
                in_generated = False
            continue
        kept.append(line)
    return kept


def frontmatter_paths(lines: list[str]) -> list[str]:
    paths: list[str] = []
    in_paths = False
    for line in lines:
        stripped = line.strip()
        if stripped == "paths:":
            in_paths = True
            continue
        if stripped.endswith(":") and not stripped.startswith("- "):
            in_paths = False
            continue
        if in_paths and stripped.startswith("- "):
            paths.append(stripped[2:].strip().strip('"').strip("'"))
    return paths


def insert_generated_project_paths(frontmatter: str, paths: list[str]) -> str:
    lines = strip_generated_project_paths(frontmatter.splitlines())
    existing = set(frontmatter_paths(lines))
    generated = [path for path in paths if path not in existing]

    if not generated:
        return "\n".join(lines).rstrip()

    path_index = next((i for i, line in enumerate(lines) if line.strip() == "paths:"), None)
    if path_index is None:
        lines = ["paths:"] + lines
        path_index = 0

    insert_at = path_index + 1
    while insert_at < len(lines):
        stripped = lines[insert_at].strip()
        if stripped and not stripped.startswith("- ") and not stripped.startswith("#"):
            break
        insert_at += 1

    block = [
        f"  {GENERATED_PROJECT_PATHS_BEGIN}",
        *[f'  - "{path}"' for path in generated],
        f"  {GENERATED_PROJECT_PATHS_END}",
    ]
    return "\n".join(lines[:insert_at] + block + lines[insert_at:]).rstrip()


def sync_claude_rule_project_paths(root: Path, rules: list[dict[str, object]]) -> None:
    rules_dir = root / ".claude" / "rules"
    if not rules_dir.is_dir():
        return

    by_pointer = generated_paths_by_pointer(rules)
    for pointer_path in sorted(rules_dir.glob("*.md")):
        name = pointer_path.stem
        text = read_text(pointer_path)
        match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, flags=re.DOTALL)
        if match:
            frontmatter, body = match.group(1), match.group(2)
        else:
            frontmatter, body = "paths:", text
        new_frontmatter = insert_generated_project_paths(frontmatter, by_pointer.get(name, []))
        body_text = body.lstrip("\n")
        pointer_path.write_text(f"---\n{new_frontmatter}\n---\n\n{body_text}", encoding="utf-8")


def write_drift_map_candidates(root: Path, paths: dict[str, list[str]]) -> int:
    drift_path = root / ".agent" / "drift-map.yml"
    text = read_text(drift_path)
    block = generated_drift_block(paths)
    pattern = re.compile(
        r"\n?# BEGIN GENERATED PROJECT DRIFT CANDIDATES\n.*?# END GENERATED PROJECT DRIFT CANDIDATES\n?",
        re.DOTALL,
    )
    if pattern.search(text):
        new_text = pattern.sub("\n" + block + "\n", text)
    else:
        marker = "rules:\n"
        if marker in text:
            new_text = text.replace(marker, marker + block + "\n\n", 1)
        else:
            new_text = text.rstrip() + "\n\nrules:\n" + block + "\n"
    drift_path.write_text(new_text.rstrip() + "\n", encoding="utf-8")
    return block.count("  - name:")


def write_report(root: Path, project: dict[str, object], commands: list[tuple[str, str, str]], clues: list[str], drift_candidate_count: int) -> None:
    git_root = run_git(root, ["rev-parse", "--show-toplevel"])
    branch = run_git(root, ["branch", "--show-current"])
    report = [
        "# Bootstrap Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "## Evidence Sources",
        "",
        f"- Project root: `{root}`",
        f"- Git root: `{git_root or 'not detected'}`",
        f"- Git branch: `{branch or 'not detected'}`",
        "",
        "## Auto-Detected Facts",
        "",
        f"- Project types: {', '.join(project.get('detected') or []) or 'none detected'}",
        f"- lproj languages: {', '.join(project.get('lproj') or []) or 'none detected'}",
        f"- locale folders: {', '.join(project.get('locales') or []) or 'none detected'}",
        f"- command candidates: {len(commands)}",
        f"- drift-map project candidate rules: {drift_candidate_count}",
        "",
        "## Old Rule Clues",
        "",
    ]
    if clues:
        report.extend(f"- {clue}" for clue in clues)
    else:
        report.append("- no old AGENTS/CLAUDE backups detected")

    report.extend(
        [
            "",
            "## Needs Review",
            "",
            "- Fill `.agent/product-invariants.md` with durable product principles.",
            "- Fill `.agent/user-journeys.md` with the project's core user paths.",
            "- Review `.agent/command-contract.md` and replace invalid command candidates.",
            "- Review generated candidates in `.agent/drift-map.yml` for project-specific path ownership and noise.",
            "- Review installed hook configs in `.codex/hooks.json` and `.claude/settings.json` if this project needs local customization.",
            "- Do not treat device, store, production, remote, pricing, or credential state as verified from this bootstrap.",
        ]
    )
    (root / ".agent" / "bootstrap-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def write_adaptation_evidence(root: Path, project: dict[str, object], commands: list[tuple[str, str, str]], clues: list[str], drift_candidate_count: int) -> None:
    review_path = root / ".agent" / "adaptation-review.md"
    if not review_path.exists():
        return

    evidence = [
        "# BEGIN GENERATED ADAPTATION EVIDENCE",
        "# Generated by scripts/bootstrap-project-context.py.",
        "# This is scanner evidence for agent review, not proof that adaptation is complete.",
        f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Project types: {', '.join(project.get('detected') or []) or 'none detected'}",
        f"- lproj languages: {', '.join(project.get('lproj') or []) or 'none detected'}",
        f"- locale folders: {', '.join(project.get('locales') or []) or 'none detected'}",
        f"- command candidates: {len(commands)}",
        f"- drift-map project candidate rules: {drift_candidate_count}",
        f"- old rule backup clues: {len(clues)}",
        "# END GENERATED ADAPTATION EVIDENCE",
    ]

    text = read_text(review_path)
    block = "\n".join(evidence)
    pattern = re.compile(
        r"\n?# BEGIN GENERATED ADAPTATION EVIDENCE\n.*?# END GENERATED ADAPTATION EVIDENCE\n?",
        re.DOTALL,
    )
    if pattern.search(text):
        new_text = pattern.sub("\n" + block + "\n", text)
    else:
        new_text = text.rstrip() + "\n\n" + block + "\n"
    review_path.write_text(new_text.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap project-specific Rules context.")
    parser.add_argument("--target", default=".", help="Project root. Defaults to cwd.")
    args = parser.parse_args()

    root = Path(args.target).resolve()
    if not (root / ".agent").exists():
        print("FAIL: .agent directory not found. Install Rules first.", file=sys.stderr)
        return 1

    files = find_files(root)
    project = detect_project(root, files)
    paths = classify_paths(root, files)
    commands = command_candidates(root)
    clues = old_rule_clues(root)
    adapted = is_adapted(root)

    write_project_map(root, project, paths, commands)
    write_command_contract(root, commands)
    project_rules = project_drift_rules(paths)
    if adapted:
        drift_candidate_count = len(project_rules)
    else:
        drift_candidate_count = write_drift_map_candidates(root, paths)
        sync_claude_rule_project_paths(root, project_rules)
    write_report(root, project, commands, clues, drift_candidate_count)
    write_adaptation_evidence(root, project, commands, clues, drift_candidate_count)

    print("Bootstrap complete:")
    print("  - .agent/project-map.md")
    print("  - .agent/command-contract.md")
    if adapted:
        print("  - .agent/drift-map.yml (left unchanged; project is already adapted)")
        print("  - .claude/rules/*.md (left unchanged; project is already adapted)")
    else:
        print("  - .agent/drift-map.yml")
        print("  - .claude/rules/*.md")
    print("  - .agent/bootstrap-report.md")
    print("  - .agent/adaptation-review.md")
    suggest_script = root / "scripts" / "suggest-rule-updates.py"
    if suggest_script.exists():
        subprocess.run([sys.executable, str(suggest_script), "--quiet"], cwd=root, check=False)
        print("  - .agent/rule-candidates.md")
    print("Review these files before treating candidates as durable rules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
