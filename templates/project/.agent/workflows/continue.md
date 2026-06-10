# Workflow: Continue

Use when taking over unfinished work from Claude, Codex, a human, or a prior session.

## Steps

1. Read `.agent/work/current.md` if present — it is intent and risk context, not proof.
2. Reconstruct actual state from `git status`, the current diff, and the files themselves; protect user-owned local changes you cannot attribute.
3. Check the candidate inbox: pending items in `.agent/rule-candidates.md` carry forward across commits and handoffs — they are part of the work you inherit (`.agent/index.md`, At Finalize).
4. Continue via the implement or review workflow; update or clear the handoff when the state changes.
