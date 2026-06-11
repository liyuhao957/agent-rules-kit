# Agent Index

Routing map for the shared project protocol. Load only what the current task needs; every doc is a map, not proof — verify against current code before relying on it.

## Task Lifecycle

1. **Start**: if `.agent/adaptation-review.md` says `Status: pending`, run `.agent/workflows/adapt-rules.md` before ordinary work.
2. **Route**: pick the workflow for the task type and the domain docs for the touched areas (tables below).
3. **Implement**: smallest change that closes the user-visible loop; verify doc claims against current code first.
4. **Finalize**: follow "At Finalize" below — the canonical protocol.
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
| README, user-facing docs | `.agent/user-journeys.md` + `.agent/command-contract.md` |

After editing, `python3 scripts/check-doc-drift.py` lists the mapped docs for your actual diff — prefer that mechanical list over loading everything.

## At Finalize

Canonical finalize protocol. Other docs point here; do not restate it elsewhere.

1. Apply `.agent/quality-gates.md` to the affected loops; choose evidence with `.agent/verification-map.md` and commands from `.agent/command-contract.md`.
2. Run `python3 scripts/check-doc-drift.py` — advisory list of shared docs mapped to your diff (policy: `.agent/doc-drift.md`).
3. Run `python3 scripts/suggest-rule-updates.py` — regenerates the candidate inbox `.agent/rule-candidates.md`.
4. The Stop gate blocks finalization only on pending high-risk (`risk:*`) candidates — secrets, billing, release, production. Resolve those with one of four statuses plus a real decision note: `promoted` (fact written into the right `.agent/*` doc), `checked-unchanged`, `rejected`, or `needs-user` (high-risk, unprovable from repo/tool evidence). Drift and command candidates are advisory — resolve when useful; they never block.

Inbox semantics that matter:

- A status flipped without a real decision note reverts to pending on the next scan.
- Resolved candidates move to the compact archive section of `.agent/rule-candidates.md` (the audit trail); rejected items stay suppressed.
- High-risk candidates carry forward across regeneration, commits, and handoffs. Committing does not clear them.
- One candidate per rule (`risk:billing`, `drift:ui-copy`) — a stable id, not one per changed-file set. It reopens only when the rule fires on genuinely new evidence (its `EvidenceKey` changes).
- `.agent/rule-candidates.md` is a local working inbox; gitignore it (see README) so its churn never lands in commits.

Full engine mechanics: `.agent/doc-drift.md`.

## Reference (load when the topic comes up)

- Durable product promises: `.agent/product-invariants.md`
- Core user paths: `.agent/user-journeys.md`
- Memory / skills / tools policies: `.agent/memory-policy.md`, `.agent/skill-policy.md`, `.agent/tool-policy.md`
- Rules maintenance: `.agent/rule-health.md`
- Long-lived decisions: `.agent/decisions/`
- Auto-generated map and report: `.agent/project-map.md`, `.agent/bootstrap-report.md`
- Adaptation status: `.agent/adaptation-review.md`
- Outside practices absorbed into this kit: `.agent/external-practices.md`
