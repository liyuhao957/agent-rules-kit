---
name: continue
description: Use when the agent is continuing unfinished work from another agent (Claude or Codex), another session, a human, or a previous handoff. Reconstruct state from current files and git before proceeding.
---

# Continue

1. Follow `.agent/workflows/continue.md`.
2. Reconstruct state from `git status` and the current diff; `.agent/work/current.md` is intent and risk context, not proof.
3. Protect user-owned local changes; never revert work you cannot attribute.
4. Then continue via the implement or review-changes workflow.
