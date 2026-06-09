# Workflow: Review

Use when checking existing changes, especially changes made by another agent.

## Steps

1. Identify the user's intended outcome.
2. Inspect current `git status` and diff.
3. Treat previous summaries and handoffs as context, not proof.
4. Read only relevant workflow/domain docs.
5. Check behavior, regressions, data/state, UI/copy, verification, and doc drift.
6. Run `python3 scripts/check-doc-drift.py` when reviewing a local diff that may change durable project facts.
7. Run `python3 scripts/suggest-rule-updates.py` and handle `.agent/rule-candidates.md` autonomously:
   - promote verified durable facts into `.agent/*`
   - mark covered candidates `checked-unchanged`
   - mark non-durable candidates `rejected`
   - mark unprovable high-risk facts `needs-user`
8. Prioritize findings by severity and cite concrete files/lines when possible.
9. If asked to fix directly, patch, validate, and summarize the fix.

## Review Output

Lead with findings. If there are no issues, say so clearly and list residual risk or test gaps.
