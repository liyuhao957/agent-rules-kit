---
name: adapt-rules
description: Use when Codex is asked to install, bootstrap, adapt, migrate, or initialize Rules for this project, especially when .agent/adaptation-review.md is pending. The agent must inspect current code/config and write verified project-specific rules.
---

# Adapt Rules

Use this skill after installing Rules or when `.agent/adaptation-review.md` says `Status: pending`.

## Workflow

1. Read `AGENTS.md`, `.agent/index.md`, and `.agent/workflows/adapt-rules.md`.
2. Run `python3 scripts/bootstrap-project-context.py` if bootstrap output is missing or stale.
3. Treat `.agent/project-map.md`, `.agent/bootstrap-report.md`, and old backups as clues, not proof.
4. Inspect current code/config/tests/scripts/docs before writing durable project facts.
5. Update `.agent/product-invariants.md`, `.agent/user-journeys.md`, `.agent/command-contract.md`, relevant `.agent/domains/*`, and `.agent/drift-map.yml`.
6. Run `python3 scripts/suggest-rule-updates.py` and handle every `.agent/rule-candidates.md` candidate autonomously.
7. Fill `.agent/adaptation-review.md`, mark `Status: adapted`, and list unverified facts explicitly.
8. Run `bash /Users/ct/code/Rules/scripts/validate-installed-project.sh . --require-adapted --require-candidates-reviewed`.
