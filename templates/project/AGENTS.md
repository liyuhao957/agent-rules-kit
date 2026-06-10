# Project Agent Contract

Shared entrypoint for Codex, Claude Code (via `CLAUDE.md`), and any coding agent in this repository.

## Read First

- If `.agent/adaptation-review.md` says `Status: pending`, run `.agent/workflows/adapt-rules.md` first. Installed templates are not project rules until an agent has verified them against current code.
- Current code, config, tests, and tool output beat docs, memories, handoffs, and another agent's summary. Verify task-critical claims before acting; docs are navigation, not proof.
- Documented commands are examples until verified; `.agent/command-contract.md` holds the verified inventory.

## On-Demand Context Routing

- Load context on demand, not up front. `.agent/index.md` routes by task type and touched area.
- Claude Code auto-loads path-scoped pointers from `.claude/rules/`; Codex gets the same pointers from its PostToolUse hook.
- After editing, `python3 scripts/check-doc-drift.py` mechanically lists which shared docs map to your diff — use that list instead of guessing or loading everything.

## Finalize

- Apply `.agent/quality-gates.md`: done means the affected loops are closed or explicitly marked unverified. Two loops never skip — drift (durable facts changed → shared docs updated or called out) and rule growth (no pending candidates).
- Run `python3 scripts/suggest-rule-updates.py`; resolve every candidate in `.agent/rule-candidates.md` as `promoted`, `checked-unchanged`, `rejected`, or `needs-user`, each with a real decision note.
- Pending candidates carry forward: committing does not clear them, and the Stop gate blocks on committed-but-pending items too. Full protocol: `.agent/index.md` (At Finalize).

## Cross-Agent Handoff

- Claude Code and Codex may implement, review, continue, or close in any order. Inspect `git status` and the real diff before continuing or reviewing.
- When stopping mid-task, write `.agent/work/current.md` using `.agent/handoff-template.md`. Handoff notes are intent and risk, not proof.
- Private Claude memory and private Codex memory are not shared project truth. Durable rules stay in repository-visible `AGENTS.md` and `.agent/*`; skills and pointers load them, never replace them.

## Boundaries And Tools

- Ask before actions affecting product direction, data safety, irreversible deletion, billing/pricing, external users, release, or production state; decide ordinary implementation details yourself and explain at the end.
- Skills are workflow loaders, not guarantees; live or remote state requires real tool output, never inference.
- After installing Rules or large structure changes, `python3 scripts/bootstrap-project-context.py` refreshes the generated project context.
- When changing the rules themselves, apply `.agent/rule-health.md`.
