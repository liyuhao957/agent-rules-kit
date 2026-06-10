---
name: doc-drift
description: Use when changes may have made shared project docs stale, when deciding whether AGENTS, .agent docs, skills, hooks, or drift-map need updates, or to run and interpret the doc-drift detector.
---

# Doc Drift

1. Run `python3 scripts/check-doc-drift.py` (advisory: lists the shared docs mapped to changed paths).
2. Apply `.agent/doc-drift.md` to each signal: updated, checked unchanged, out of scope, or not checked.
3. Run `python3 scripts/suggest-rule-updates.py` and resolve `.agent/rule-candidates.md` per `.agent/index.md` (At Finalize).
4. When you adjust `.agent/drift-map.yml` globs, mirror them into `.claude/rules/*.md` frontmatter.
