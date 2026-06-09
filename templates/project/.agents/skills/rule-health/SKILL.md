---
name: rule-health
description: Use when Codex is asked to improve, audit, prune, or maintain project rules, AGENTS/CLAUDE, .agent docs, skills, hooks, or drift-map quality. Checks whether rules are useful, current, scoped, and not too noisy.
---

# Rule Health

Use this skill for maintaining the rules themselves.

## Workflow

1. Read `.agent/rule-health.md`.
2. Inspect the relevant rule docs, skills, hooks, and drift-map entries.
3. Identify stale, duplicated, over-specific, noisy, or unenforced rules.
4. Rewrite, move, or delete rules when the current evidence supports it.
5. Run `bash scripts/validate-rules-template.sh` when working in the rules-kit repo, or the target project's equivalent validation.

