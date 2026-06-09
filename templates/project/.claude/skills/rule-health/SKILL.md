---
name: rule-health
description: Use when Claude Code is asked to improve, audit, prune, or maintain project rules, AGENTS/CLAUDE, .agent docs, skills, hooks, or drift-map quality. Checks whether rules are useful, current, scoped, and not too noisy.
---

# Rule Health

Use this skill for maintaining the rules themselves.

## Workflow

1. Read `.agent/rule-health.md`.
2. Inspect the relevant rule docs, skills, hooks, and drift-map entries.
3. Identify stale, duplicated, over-specific, noisy, or unenforced rules.
4. Rewrite, move, or delete rules when the current evidence supports it.
5. Run the target project's rules validation when available.

