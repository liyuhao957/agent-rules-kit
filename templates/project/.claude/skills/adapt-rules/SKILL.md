---
name: adapt-rules
description: Use when asked to install, bootstrap, adapt, migrate, or initialize Rules for this project, especially when .agent/adaptation-review.md says pending. Inspect current code/config and write verified project-specific rules.
---

# Adapt Rules

1. Follow `.agent/workflows/adapt-rules.md` end to end.
2. Promote only facts verified against current code/config/tool output; mark unprovable high-risk facts `needs-user`.
3. Tighten `.agent/drift-map.yml` globs for this project and mirror them into `.claude/rules/*.md` frontmatter.
4. Validate using the rules-kit clone recorded in `.agent/rules-kit.json` (`source` field): `bash <source>/scripts/validate-installed-project.sh . --require-adapted --require-candidates-reviewed`.
