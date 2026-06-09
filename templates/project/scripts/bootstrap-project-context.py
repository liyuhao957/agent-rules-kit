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


def classify_paths(root: Path, files: list[Path]) -> dict[str, list[str]]:
    rels = [rel(path, root) for path in files]

    def pick(patterns: tuple[str, ...], limit: int = 20) -> list[str]:
        matches: list[str] = []
        for item in rels:
            lower = item.lower()
            if any(pattern.lower() in lower for pattern in patterns):
                matches.append(item)
        return sorted(matches)[:limit]

    return {
        "ui": pick(("/views/", "/view/", "/components/", "/component/", "/screens/", "/screen/", "view.", "screen.", "component.")),
        "models": pick(("/models/", "/model/", "model.", "schema", "migration")),
        "services": pick(("/services/", "/service/", "sync", "backup", "import", "export")),
        "tests": pick(("/tests/", "test.", "tests.", "spec.")),
        "release": pick(("fastlane", "exportoptions", "entitlements", ".github/workflows", "release", "deploy", "signing")),
        "localization": pick((".lproj/", "locales/", "/locales/", "locale/", "/locale/", "i18n/", "/i18n/", "translations/", "/translations/", "localizable.strings", ".strings", ".xliff", ".arb")),
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
        parent_parts = parts[:-1] if Path(value).suffix else parts
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


def generated_drift_block(paths: dict[str, list[str]]) -> str:
    mapping = {
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
            "Project-specific service/sync/backup/import/export paths detected by bootstrap.",
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

    lines = [
        "# BEGIN GENERATED PROJECT DRIFT CANDIDATES",
        "# Generated by scripts/bootstrap-project-context.py.",
        "# Review these candidates; they are path signals, not proof docs must change.",
    ]
    any_rule = False
    for key, (name, docs, reason) in mapping.items():
        candidates = top_dirs(paths.get(key, []))
        if not candidates:
            continue
        any_rule = True
        lines.extend(
            [
                f"  - name: {name}",
                "    paths:",
            ]
        )
        lines.extend(f'      - "{candidate}"' for candidate in candidates)
        lines.append("    docs:")
        lines.extend(f'      - "{doc}"' for doc in docs)
        lines.append(f'    reason: "{reason}"')
        lines.append("")
    if not any_rule:
        lines.append("  # No project-specific candidates detected yet.")
    lines.append("# END GENERATED PROJECT DRIFT CANDIDATES")
    return "\n".join(lines).rstrip()


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
            "- Decide whether to enable hook examples by copying `.codex/hooks.example.json` to `.codex/hooks.json` and/or `.claude/settings.example.json` to `.claude/settings.json`.",
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

    write_project_map(root, project, paths, commands)
    write_command_contract(root, commands)
    drift_candidate_count = write_drift_map_candidates(root, paths)
    write_report(root, project, commands, clues, drift_candidate_count)
    write_adaptation_evidence(root, project, commands, clues, drift_candidate_count)

    print("Bootstrap complete:")
    print("  - .agent/project-map.md")
    print("  - .agent/command-contract.md")
    print("  - .agent/drift-map.yml")
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
