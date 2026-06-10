---
name: review-changes
description: Use when the agent is asked to review, audit, check, critique, validate, or inspect code or changes, especially changes made by another agent (Claude or Codex). Inspect the actual diff and evidence instead of trusting summaries.
---

# Review Changes

1. Follow `.agent/workflows/review.md`.
2. Inspect `git status` and the real diff first; treat handoffs and another agent's summary as clues, not proof.
3. Check the `.agent/quality-gates.md` loops the change touches.
4. Lead with findings ordered by severity, cite files/lines, and state residual risk and test gaps.
