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


def command_segments(command: str) -> list[str]:
    return [segment.strip() for segment in re.split(r"\n|&&|\|\||;", command) if segment.strip()]


def split_command(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def is_read_only_lookup(tokens: list[str]) -> bool:
    if not tokens:
        return False
    first = basename(tokens[0])
    if first in READ_ONLY_COMMANDS:
        return True
    return first == "git" and len(tokens) > 1 and tokens[1] in {"diff", "show", "status", "log", "grep"}


def has_rm_rf(tokens: list[str]) -> bool:
    if not tokens or basename(tokens[0]) != "rm":
        return False
    return any(token.startswith("-") and "r" in token and "f" in token for token in tokens[1:])


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


def segment_reasons(segment: str, tokens: list[str]) -> list[str]:
    text = segment.lower()
    reasons: list[str] = []

    if is_read_only_lookup(tokens):
        return reasons

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
    if re.search(r"\b(drop\s+database|drop\s+table|truncate\s+table|delete\s+from)\b", text):
        reasons.append("destructive database statement")

    return reasons


def blocked_reasons(command: str) -> list[str]:
    reasons: list[str] = []
    for segment in command_segments(command):
        tokens = split_command(segment)
        for reason in segment_reasons(segment, tokens):
            if reason not in reasons:
                reasons.append(reason)
    return reasons


def warning_needed(command: str, reasons: list[str]) -> bool:
    if reasons:
        return True
    for segment in command_segments(command):
        tokens = split_command(segment)
        if is_read_only_lookup(tokens):
            continue
        text = segment.lower()
        warning_words = ("deploy", "release", "publish", "push", "submit", "delete", "reset", "production", "prod")
        if any(word in text for word in warning_words):
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
