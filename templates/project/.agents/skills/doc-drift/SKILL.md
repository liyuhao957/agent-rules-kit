---
name: doc-drift
description: Use when Codex changes durable project behavior or notices stale project docs. Decide whether shared docs, decisions, skills, hooks, or task protocols need updates.
---

# Doc Drift

Use this skill when project rules may need to change.

## Workflow

1. Read `.agent/doc-drift.md`.
2. Run `python3 scripts/check-doc-drift.py` and `python3 scripts/suggest-rule-updates.py` when a git diff is available.
3. Identify whether each candidate affects durable future-agent behavior.
4. Update the smallest relevant shared doc when a candidate should be promoted.
5. Mark every candidate in `.agent/rule-candidates.md` as promoted, checked-unchanged, rejected, or needs-user.
6. Do not update docs for one-off implementation details.
7. If stale docs are found but not fixed, mention the stale area in the final reply.
