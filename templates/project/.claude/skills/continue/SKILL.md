---
name: continue
description: Use when Claude Code is continuing unfinished work from Codex, another Claude session, a human, or a previous handoff. Reconstruct state from current files and git before proceeding.
---

# Continue

Use this skill when taking over unfinished work.

## Workflow

1. Read `.agent/index.md`.
2. Read `.agent/workflows/continue.md`.
3. Inspect actual `git status` and current diff first.
4. Read `.agent/work/current.md` if present, only as intent/risk context.
5. Continue with implement or review workflow as appropriate.
6. Update or clear the handoff note when state changes.

