---
name: review
description: Use when Codex is asked to review, audit, check, critique, validate, or inspect code or changes, especially changes made by another agent. Inspect actual diff and evidence instead of trusting summaries.
---

# Review

Use this skill for code review, product audit, and change validation.

## Workflow

1. Read `.agent/index.md`.
2. Read `.agent/workflows/review.md`.
3. Inspect current `git status` and diff before trusting any handoff or summary.
4. Check source-of-truth, quality gates, domain risks, and doc drift.
5. Run `python3 scripts/suggest-rule-updates.py` and handle rule candidates when reviewing durable project changes.
6. Lead with findings. If no findings, say that clearly and list test gaps or residual risk.
