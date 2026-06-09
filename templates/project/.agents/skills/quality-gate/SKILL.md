---
name: quality-gate
description: Use before finalizing non-trivial Codex work to check functional, logic, UI/copy, data, verification, and documentation-drift loops.
---

# Quality Gate

Use this skill before final response on non-trivial work.

## Workflow

1. Read `.agent/quality-gates.md`.
2. Read `.agent/verification-map.md`.
3. Read `.agent/command-contract.md` when validation commands matter.
4. Check each affected loop: intent, functional, logic, UI/copy, data, verification, drift.
5. Run `python3 scripts/check-doc-drift.py` when a git diff is available.
6. Run or inspect the smallest evidence that honestly supports completion.
7. Final reply must distinguish verified, inferred, and unverified.
