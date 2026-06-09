# Workflow: Continue

Use when taking over unfinished work from Claude, Codex, a human, or a prior session.

## Steps

1. Inspect `git status` and current diff first.
2. Read `.agent/work/current.md` if present.
3. Treat handoff as intent and risk context, not proof.
4. Reconstruct what changed from the actual files.
5. Identify user-owned or unrelated local changes.
6. Determine what is verified, inferred, and unverified.
7. Continue with the relevant implement/review workflow.
8. Update or clear the handoff when the state changes.

