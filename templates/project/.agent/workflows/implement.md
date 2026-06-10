# Workflow: Implement

Use when adding or changing behavior.

## Steps

1. Restate the outcome and identify the affected user path.
2. Inspect `git status` and relevant current code/config.
3. Load only the domain docs the task touches: route via `.agent/index.md` before editing; after editing, `python3 scripts/check-doc-drift.py` lists the mapped docs for your actual diff. (Claude auto-loads pointers via `.claude/rules/`; Codex gets them from the PostToolUse router.)
4. Verify doc claims against current evidence before relying on them.
5. Implement the smallest change that closes the requested loop.
6. Check related entry points, state transitions, UI/copy, data, and error paths.
7. Use `.agent/command-contract.md` to choose targeted validation; broaden validation when risk or blast radius is high.
8. Apply `.agent/quality-gates.md`.
9. Run `python3 scripts/check-doc-drift.py` and apply `.agent/doc-drift.md`.
10. Run `python3 scripts/suggest-rule-updates.py`, then handle every candidate in `.agent/rule-candidates.md` without asking the user unless the current task depends on an unprovable high-risk fact:
    - promote verified durable facts into the correct `.agent/*` doc and mark `promoted`
    - mark `checked-unchanged` when existing rules already cover it
    - mark `rejected` when it is not durable or useful
    - mark `needs-user` only when repo/tool evidence cannot prove a high-risk fact
11. Write `.agent/work/current.md` only if work remains or another agent needs context.

## Final Reply

Include what changed, what was verified, and what remains unverified.
