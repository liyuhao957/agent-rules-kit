---
paths:
  - "AGENTS.md"
  - "CLAUDE.md"
  - ".agent/**"
  - ".agents/**"
  - ".claude/**"
  - ".codex/**"
---

You are editing the project rules themselves. Read `.agent/rule-health.md` first: rules must stay short, current, scoped, and low-noise. When you change globs in `.agent/drift-map.yml`, mirror them into `.claude/rules/*.md` frontmatter. Durable rules live in repo-visible markdown, not private agent memory.
