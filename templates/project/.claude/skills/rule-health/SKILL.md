---
name: rule-health
description: Use when asked to improve, audit, prune, or maintain the project rules themselves, AGENTS/CLAUDE, .agent docs, .claude/rules, skills, hooks, or drift-map quality.
---

# Rule Health

1. Apply `.agent/rule-health.md`: keep, rewrite, move, or delete each rule.
2. Rules must stay short, current, scoped, and low-noise; tighten noisy drift globs instead of tolerating them.
3. Keep `.agent/drift-map.yml` and `.claude/rules/*.md` globs mirrored.
4. Durable rules stay in repo-visible markdown; private agent memory is never the rule source.
