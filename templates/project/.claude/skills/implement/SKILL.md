---
name: implement
description: Use when Claude Code is asked to add, change, or fix product behavior, code, UI, data flow, or tests in this project. Follow shared source-of-truth, quality gates, doc drift, and relevant domain protocols before finalizing.
---

# Implement

Use this skill for ordinary implementation and bug-fix work.

## Workflow

1. Read `.agent/index.md`.
2. Read `.agent/workflows/implement.md`.
3. Read relevant `.agent/domains/*` docs for the task.
4. Verify doc claims against current code/config/tool output before editing.
5. Implement the smallest change that closes the requested user path.
6. Use `.agent/command-contract.md` to choose validation.
7. Apply `.agent/quality-gates.md` and `.agent/doc-drift.md`.
8. Run `python3 scripts/suggest-rule-updates.py` and handle `.agent/rule-candidates.md` without asking the user for ordinary candidates.
9. Final reply must state changed files, verification evidence, rule-candidate handling, and unverified risk.
