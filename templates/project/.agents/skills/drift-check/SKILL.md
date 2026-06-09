---
name: drift-check
description: Use when Codex needs to determine whether current code/config changes may require updates to AGENTS, CLAUDE, .agent docs, skills, hooks, or shared project rules. Runs the doc drift detector and interprets the result.
---

# Drift Check

Use this skill when the question is "do rules/docs need updates?" or before closing non-trivial work.

## Workflow

1. Run `python3 scripts/check-doc-drift.py`.
2. Run `python3 scripts/suggest-rule-updates.py`.
3. For each candidate, decide: promoted, checked-unchanged, rejected, or needs-user.
4. Update the smallest relevant shared doc when durable project behavior changed.
5. Do not update docs just because a path matched.
6. Report the candidate handling result in the final reply.
