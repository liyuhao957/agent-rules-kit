# Agent Index

This directory is the shared project protocol for Claude Code and Codex.

Read this file for non-trivial work, then load only the workflow and domain docs that match the task.

## Always Apply

- `.agent/adaptation-review.md`
- `.agent/source-of-truth.md`
- `.agent/quality-gates.md`
- `.agent/memory-policy.md`
- `.agent/skill-policy.md`
- `.agent/tool-policy.md`
- `.agent/command-contract.md`
- `.agent/doc-drift.md`
- `.agent/drift-map.yml`
- `.agent/rule-candidates.md`
- `.agent/rule-health.md`

## Workflows

- Installing/adapting Rules: `.agent/workflows/adapt-rules.md`
- Implementing or fixing: `.agent/workflows/implement.md`
- Reviewing another change: `.agent/workflows/review.md`
- Continuing unfinished work: `.agent/workflows/continue.md`
- Release or external-state work: `.agent/workflows/release.md`

## Domains

- UI, UX, copy: `.agent/domains/ui-copy.md`
- Build, test, device, local runtime: `.agent/domains/build-test.md`
- Data, persistence, sync, migration, backup, destructive flows: `.agent/domains/data-sync.md`
- Localization and user-visible strings: `.agent/domains/localization.md`
- Performance and scalability: `.agent/domains/performance.md`
- Release, store, publishing, production operations: `.agent/domains/release.md`

## Shared Product Context

- Durable product principles: `.agent/product-invariants.md`
- Core user paths: `.agent/user-journeys.md`
- Auto-generated project map: `.agent/project-map.md`
- Auto-generated bootstrap review report: `.agent/bootstrap-report.md`
- Rules adaptation status: `.agent/adaptation-review.md`
- Long-lived decisions: `.agent/decisions/`
- Temporary handoff notes: `.agent/work/current.md` when present
- Documentation drift discovery: `python3 scripts/check-doc-drift.py`
- Automatic rule-growth inbox: `.agent/rule-candidates.md` via `python3 scripts/suggest-rule-updates.py`
- Current validation command inventory: `.agent/command-contract.md`
- Rules-kit maintenance principles: `.agent/rule-health.md`
- Outside practices absorbed into this kit: `.agent/external-practices.md`

## Rule

Every task-specific doc is a map, not proof. After reading it, verify the relevant facts in the current repo or real tool output before editing or reporting.
