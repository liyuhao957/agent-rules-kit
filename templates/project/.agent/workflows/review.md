# Workflow: Review

Use when checking existing changes, especially changes made by another agent.

## Steps

1. Identify the user's intended outcome, then inspect current `git status` and the real diff. Previous summaries and handoffs are clues, not proof — verify claims against the diff and current code.
2. Check the `.agent/quality-gates.md` loops the change touches; load only relevant workflow/domain docs.
3. If the diff may change durable project facts, finalize per `.agent/index.md` (At Finalize): drift check, candidate scan, candidates resolved.
4. Lead with findings ordered by severity, cite concrete files/lines, and state residual risk and test gaps. If there are no issues, say so clearly.
5. If asked to fix directly, patch, validate, and summarize the fix.
