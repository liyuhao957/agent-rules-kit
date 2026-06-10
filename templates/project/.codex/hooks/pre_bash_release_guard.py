#!/usr/bin/env python3
"""PreToolUse hook for high-risk shell commands.

Blocks a small set of high-risk commands by default.
Set RULES_HOOK_ALLOW_RISK=1 to bypass after explicit scope and live-state
verification.
"""

from __future__ import annotations

import json
import os
from pathlib import PurePath
import re
import shlex
import sys


TRUE_VALUES = {"1", "true", "yes", "allow", "bypass"}
READ_ONLY_COMMANDS = {
    "awk",
    "cat",
    "echo",
    "find",
    "grep",
    "head",
    "ls",
    "nl",
    "printf",
    "rg",
    "sed",
    "tail",
    "wc",
}
EPHEMERAL_DELETE_DIRS = {
    "node_modules",
    "dist",
    "build",
    "out",
    "coverage",
    ".next",
    ".nuxt",
    ".turbo",
    ".cache",
    ".parcel-cache",
    "__pycache__",
    ".pytest_cache",
    "DerivedData",
}
REMOTE_DB_COMMANDS = {"psql", "mysql", "mariadb", "mongosh"}
WARNING_WORDS = {
    "deploy",
    "release",
    "publish",
    "push",
    "submit",
    "delete",
    "reset",
    "production",
    "prod",
}
HEREDOC_OPEN = re.compile(r"(?<!<)<<(?!<)-?\s*(['\"]?)(\w+)\1")


def bypass_enabled() -> bool:
    return os.environ.get("RULES_HOOK_ALLOW_RISK", "").strip().lower() in TRUE_VALUES


def basename(value: str) -> str:
    return PurePath(value).name.lower()


def extract_commands(value: object) -> list[str]:
    commands: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"command", "cmd"} and isinstance(child, str):
                commands.append(child)
            else:
                commands.extend(extract_commands(child))
    elif isinstance(value, list):
        for child in value:
            commands.extend(extract_commands(child))
    return commands


def payload_command() -> str:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return raw

    commands = extract_commands(payload)
    if commands:
        return "\n".join(commands)
    return json.dumps(payload, ensure_ascii=False)


def strip_heredoc_bodies(command: str) -> str:
    """Drop heredoc body lines so document text is not matched as commands."""
    kept: list[str] = []
    pending: list[str] = []
    for line in command.split("\n"):
        if pending:
            if line.strip() == pending[0]:
                pending.pop(0)
            continue
        kept.append(line)
        pending = [match.group(2) for match in HEREDOC_OPEN.finditer(line)]
    return "\n".join(kept)


def command_segments(command: str) -> list[str]:
    return [segment.strip() for segment in re.split(r"\n|&&|\|\||;", command) if segment.strip()]


def split_command(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def unwrap_runners(tokens: list[str]) -> list[str]:
    """Peel npx/bunx/env and pnpm/yarn dlx so wrapped commands are checked directly."""
    rest = list(tokens)
    while rest:
        first = basename(rest[0])
        if first in {"npx", "bunx", "env"}:
            tail = rest[1:]
            while tail and (tail[0].startswith("-") or (first == "env" and "=" in tail[0])):
                tail = tail[1:]
            rest = tail
            continue
        if first in {"pnpm", "yarn"} and len(rest) > 1 and rest[1] == "dlx":
            rest = rest[2:]
            continue
        break
    return rest


def shell_inline_command(tokens: list[str]) -> str:
    """Return the string passed to sh/bash/zsh -c, or "" when there is none."""
    if not tokens or basename(tokens[0]) not in {"sh", "bash", "zsh"}:
        return ""
    for index, token in enumerate(tokens[1:], start=1):
        if not token.startswith("-"):
            return ""
        if not token.startswith("--") and "c" in token:
            return tokens[index + 1] if index + 1 < len(tokens) else ""
    return ""


def is_read_only_lookup(tokens: list[str]) -> bool:
    if not tokens:
        return False
    first = basename(tokens[0])
    if first in READ_ONLY_COMMANDS:
        return True
    return first == "git" and len(tokens) > 1 and tokens[1] in {"diff", "show", "status", "log", "grep"}


def is_ephemeral_delete_target(value: str) -> bool:
    if value.startswith(("/", "~")):
        return False
    parts = PurePath(value).parts
    if not parts or ".." in parts:
        return False
    return parts[0] in EPHEMERAL_DELETE_DIRS


def has_rm_rf(tokens: list[str]) -> bool:
    if not tokens or basename(tokens[0]) != "rm":
        return False
    flags = [token for token in tokens[1:] if token.startswith("-")]
    short_flags = "".join(flag for flag in flags if not flag.startswith("--"))
    recursive = "--recursive" in flags or "r" in short_flags or "R" in short_flags
    force = "--force" in flags or "f" in short_flags
    if not (recursive and force):
        return False
    targets = [token for token in tokens[1:] if not token.startswith("-")]
    if targets and all(is_ephemeral_delete_target(target) for target in targets):
        return False
    return True


def has_git_clean_force(tokens: list[str]) -> bool:
    if len(tokens) < 3 or basename(tokens[0]) != "git" or tokens[1] != "clean":
        return False
    flag_text = "".join(token for token in tokens[2:] if token.startswith("-"))
    return "f" in flag_text and "d" in flag_text


def has_release_action(tokens: list[str]) -> bool:
    if not tokens:
        return False
    first = basename(tokens[0])
    lowered = [token.lower() for token in tokens]
    args = lowered[1:]

    if first in {"deploy", "release", "publish", "submit"}:
        return True
    if first in {"npm", "pnpm", "bun"}:
        return "publish" in args or any(arg in {"deploy", "release", "submit"} for arg in args)
    if first == "yarn":
        return "publish" in args or any(arg in {"deploy", "release", "submit"} for arg in args)
    if first in {"make", "just"}:
        return any(arg in {"deploy", "release", "publish", "submit", "prod", "production"} for arg in args)
    if first == "fastlane":
        return any(arg in {"deliver", "pilot", "release", "deploy", "submit", "upload"} for arg in args)
    if first == "asc":
        return any(arg in {"submit", "release", "publish"} for arg in args)
    if first == "gh" and len(lowered) > 2 and lowered[1] == "release":
        return lowered[2] in {"create", "upload", "edit", "delete"}
    if first in {"firebase", "vercel", "netlify", "eas"}:
        return any(arg in {"deploy", "submit", "--prod", "production"} for arg in args)
    return False


def has_prod_mutation(tokens: list[str]) -> bool:
    if not tokens:
        return False
    lowered = [token.lower() for token in tokens]
    first = basename(tokens[0])
    has_prod = any(token in {"prod", "production", "--prod"} or "production" in token for token in lowered)
    has_mutation = any(token in {"apply", "delete", "deploy", "destroy", "migrate", "release", "submit"} for token in lowered)
    return has_prod and has_mutation and first in {"kubectl", "terraform", "supabase", "firebase", "psql", "mysql"}


def segment_words(segment: str) -> set[str]:
    """Lowercased whole words with camelCase boundaries split, so "prod" never
    matches ProductCard."""
    split_camel = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", segment)
    split_acronym = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "-", split_camel)
    return set(re.findall(r"[a-z0-9]+", split_acronym.lower()))


def segment_reasons(segment: str, tokens: list[str]) -> list[str]:
    text = segment.lower()
    tokens = unwrap_runners(tokens)
    reasons: list[str] = []

    if is_read_only_lookup(tokens):
        return reasons

    inline = shell_inline_command(tokens)
    if inline:
        reasons.extend(blocked_reasons(inline))

    if re.search(r"\bgit\s+push\b(?=.*(?:--force-with-lease|--force|-f\b))", text, flags=re.DOTALL):
        reasons.append("force-pushing changes")
    if re.search(r"\bgit\s+reset\s+--hard\b", text):
        reasons.append("resetting the working tree with git reset --hard")
    if has_git_clean_force(tokens):
        reasons.append("deleting untracked files with git clean")
    if has_rm_rf(tokens):
        reasons.append("recursive forced deletion with rm -rf")
    if has_release_action(tokens):
        reasons.append("release, deploy, publish, or submit action")
    if has_prod_mutation(tokens):
        reasons.append("production-targeted mutation")
    if tokens and basename(tokens[0]) in REMOTE_DB_COMMANDS and re.search(
        r"\b(drop\s+database|drop\s+table|truncate\s+table|delete\s+from)\b", text
    ):
        reasons.append("destructive database statement")

    return reasons


def blocked_reasons(command: str) -> list[str]:
    reasons: list[str] = []
    for segment in command_segments(strip_heredoc_bodies(command)):
        tokens = split_command(segment)
        for reason in segment_reasons(segment, tokens):
            if reason not in reasons:
                reasons.append(reason)
    return reasons


def warning_needed(command: str, reasons: list[str]) -> bool:
    if reasons:
        return True
    for segment in command_segments(strip_heredoc_bodies(command)):
        tokens = split_command(segment)
        if is_read_only_lookup(tokens):
            continue
        if WARNING_WORDS & segment_words(segment):
            return True
    return False


def main() -> int:
    command = payload_command()
    reasons = blocked_reasons(command)

    if reasons and not bypass_enabled():
        print("Rules hook blocked a high-risk shell command.", file=sys.stderr)
        for reason in reasons:
            print(f"- {reason}", file=sys.stderr)
        print(
            "Verify explicit user scope, git state, auth, target, and live state first. "
            "Set RULES_HOOK_ALLOW_RISK=1 only for an intentional, verified operation.",
            file=sys.stderr,
        )
        return 2

    if reasons and bypass_enabled():
        print("Rules hook bypass: RULES_HOOK_ALLOW_RISK is set for this command.")
    elif warning_needed(command, reasons):
        print("Reminder: high-risk command signal detected. Verify scope, git state, auth, target, and live state first.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
