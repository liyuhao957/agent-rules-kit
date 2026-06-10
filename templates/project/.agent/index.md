# Agent Index

Routing map for the shared project protocol. Load only what the current task needs; every doc is a map, not proof — verify against current code before relying on it.

## Task Lifecycle

1. **Start**: if `.agent/adaptation-review.md` says `Status: pending`, run `.agent/workflows/adapt-rules.md` before ordinary work.
2. **Route**: pick the workflow for the task type and the domain docs for the touched areas (tables below).
3. **Implement**: smallest change that closes the user-visible loop; verify doc claims against current code first.
4. **Finalize**: apply `.agent/quality-gates.md`; run `python3 scripts/check-doc-drift.py` (advisory doc list) and `python3 scripts/suggest-rule-updates.py`; resolve every pending item in `.agent/rule-candidates.md`.
5. **Hand off**: write `.agent/work/current.md` (shape: `.agent/handoff-template.md`) only if work remains or another agent continues.

## By Task Type

| Task | Load |
|---|---|
| Implement or fix | `.agent/workflows/implement.md` |
| Review changes | `.agent/workflows/review.md` |
| Continue unfinished work | `.agent/workflows/continue.md` |
| Release / external state | `.agent/workflows/release.md` + `.agent/domains/release.md` |
| Install / adapt rules | `.agent/workflows/adapt-rules.md` |

## By Touched Area

Claude Code auto-loads these pointers via `.claude/rules/` when matching files are read; Codex gets them injected by the PostToolUse router hook after edits. Either way the canonical docs are:

| Area | Load |
|---|---|
| UI, components, screens, copy | `.agent/domains/ui-copy.md` |
| Data, models, migrations, sync | `.agent/domains/data-sync.md` |
| Build, test, CI, commands | `.agent/domains/build-test.md` + `.agent/command-contract.md` |
| Localization, strings | `.agent/domains/localization.md` |
| Performance, benchmarks | `.agent/domains/performance.md` |
| Release, signing, deploy, store | `.agent/domains/release.md` |

After editing, `python3 scripts/check-doc-drift.py` lists the mapped docs for your actual diff — prefer that mechanical list over loading everything.

## At Finalize

- Quality loops: `.agent/quality-gates.md`
- Evidence choices: `.agent/verification-map.md`
- Verified commands: `.agent/command-contract.md`
- Drift policy and map: `.agent/doc-drift.md`, `.agent/drift-map.yml`
- Candidate inbox (must be drained): `.agent/rule-candidates.md`

## Reference (load when the topic comes up)

- Durable product promises: `.agent/product-invariants.md`
- Core user paths: `.agent/user-journeys.md`
- Memory / skills / tools policies: `.agent/memory-policy.md`, `.agent/skill-policy.md`, `.agent/tool-policy.md`
- Rules maintenance: `.agent/rule-health.md`
- Long-lived decisions: `.agent/decisions/`
- Auto-generated map and report: `.agent/project-map.md`, `.agent/bootstrap-report.md`
- Adaptation status: `.agent/adaptation-review.md`
- Outside practices absorbed into this kit: `.agent/external-practices.md`
