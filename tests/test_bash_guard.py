#!/usr/bin/env python3
"""Contract tests for the PreToolUse bash guard.

BLOCK == exit 2, ALLOW == exit 0. Each case asserts the behavior the guard
*should* have. Cases tagged in comments with BUG were confirmed bypasses/false
positives in the 2026-06-10 review and must pass after the fix.
"""

from __future__ import annotations

import subprocess
import sys

from lib import BASH_GUARD, Results, bash_payload, run_hook

# (command, should_block, label)
CASES = [
    # --- core blocks (must stay blocking) ---
    ("git push --force origin main", True, "force push --force"),
    ("git push -f origin main", True, "force push -f"),
    ("git reset --hard HEAD~1", True, "reset --hard"),
    ("rm -rf src", True, "rm -rf source dir"),
    ("rm -rf /", True, "rm -rf root"),
    ("npm publish", True, "npm publish"),
    ("sh -c 'npm publish'", True, "wrapped npm publish"),
    ("npx vercel deploy", True, "vercel deploy"),
    ("git clean -fd", True, "git clean -fd"),
    ('psql -c "DROP TABLE users"', True, "psql drop table via -c"),

    # --- core allows (must stay allowing) ---
    ("ls -la", False, "ls"),
    ("rm -rf node_modules", False, "rm -rf node_modules (ephemeral)"),
    ("rm -rf dist build", False, "rm -rf build output"),
    ("echo production", False, "echo production (word, not action)"),
    ("git status", False, "git status"),
    ("git commit -m 'fix bug'", False, "ordinary commit"),
    ("sed -n 1p src/ProductCard.tsx", False, "ProductCard path must not trip prod"),
    ("git push origin main", False, "ordinary push"),

    # --- BUG: bypasses that must now BLOCK ---
    ("PROD=1 npm publish", True, "BUG bare env-prefix publish"),
    ("NODE_ENV=production npm publish", True, "BUG bare env-prefix publish 2"),
    ("git push origin +main", True, "BUG refspec force push"),
    ("git push origin +refs/heads/main:refs/heads/main", True, "BUG refspec force push full"),
    ("psql -h db <<SQL\nDROP TABLE users;\nSQL", True, "BUG heredoc SQL drop"),
    ("mysql appdb <<'EOF'\nDELETE FROM orders;\nEOF", True, "BUG heredoc SQL delete"),

    # --- BUG: false positives that must now ALLOW ---
    ('git commit -m "docs: warn against git reset --hard in recovery"', False, "BUG commit msg mentions reset --hard"),
    ('git commit -m "feat: add npm publish step to CI"', False, "BUG commit msg mentions publish"),

    # --- NEW: dangerous command hidden in command substitution must BLOCK ---
    ("git diff $(git push --force origin main)", True, "subst force push behind read-only"),
    ("echo `rm -rf /`", True, "backtick rm -rf root"),
    ("cat <(git reset --hard HEAD~3)", True, "process-subst reset --hard"),
]


def fail_closed_checks(results) -> None:
    """A safety guard must fail CLOSED: on unparseable/abusive input it blocks
    (exit 2), never silently allows (exit 0) or crashes (exit 1)."""
    # Deeply nested JSON (RecursionError risk).
    nested = "[" * 6000 + "]" * 6000
    code, _o, _e = run_hook(BASH_GUARD, nested)
    results.check("fail-closed on deeply nested json", code == 2, f"exit {code}")

    # Non-UTF-8 stdin must not crash the guard.
    proc = subprocess.run(
        [sys.executable, str(BASH_GUARD)],
        input=b"\xff\xfe not valid utf-8",
        capture_output=True,
    )
    results.check("non-utf-8 stdin does not crash (exit 0 or 2)", proc.returncode in (0, 2), f"exit {proc.returncode}")


def main() -> int:
    results = Results()
    for command, should_block, label in CASES:
        code, _out, _err = run_hook(BASH_GUARD, bash_payload(command))
        blocked = code == 2
        results.check(
            label,
            blocked == should_block,
            f"expected {'BLOCK' if should_block else 'ALLOW'}, got exit {code} ({command!r})",
        )
    fail_closed_checks(results)
    return results.report("bash_guard")


if __name__ == "__main__":
    raise SystemExit(main())
