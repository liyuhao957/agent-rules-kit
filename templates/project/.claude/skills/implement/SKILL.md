---
name: implement
description: Use when the agent is asked to add, change, or fix product behavior, code, UI, data flow, or tests in this project. Routes to the shared implement workflow, domain docs, and quality gates.
---

# Implement

1. Follow `.agent/workflows/implement.md`.
2. Load only the domain docs your touched paths map to: `.agent/index.md` routes by area; after editing, `python3 scripts/check-doc-drift.py` lists them mechanically.
3. Before finalizing: apply `.agent/quality-gates.md`, run `python3 scripts/suggest-rule-updates.py`, and resolve every pending item in `.agent/rule-candidates.md`.
4. Final reply: what changed, what was verified, what remains unverified.
