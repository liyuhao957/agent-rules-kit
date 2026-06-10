# Project Agent Contract

This file is the shared project entrypoint for Codex, Claude Code through `CLAUDE.md`, and any coding agent that works in this repository.

## Read First

- If `.agent/adaptation-review.md` says `Status: pending`, run `.agent/workflows/adapt-rules.md` first. Installed templates and bootstrap candidates are not project rules until an agent has verified them against current code.
- Load context on demand, not up front. `.agent/index.md` routes by task type and touched area; do not preload every `.agent/*` doc.
- Project docs are navigation and context, not proof. Verify task-critical facts in current code, config, tool output, tests, builds, or live remote state before acting.
- Do not trust another agent's summary, handoff note, memory, or old report as proof. Use them as clues.
- Treat documented commands as examples until verified; `.agent/command-contract.md` holds the verified inventory.

## Source Of Truth

Priority order:

1. The user's current explicit instruction.
2. Current repository state, code, config, tests, build output, tool output, git state, device state, and live remote state.
3. Shared project docs under `.agent/`, `AGENTS.md`, and `CLAUDE.md`.
4. README files, issues, previous handoffs, memories, and old summaries.

If docs conflict with current evidence, follow current evidence, keep the change conservative, and mention the conflict if it affected the work. Do not preserve stale implementation shape as a hard rule unless it is clearly marked as a safety constraint. Do not claim something was verified unless it was checked in the current turn.

## On-Demand Context Routing

- `.agent/index.md` is the routing map: task type → workflow doc, touched area → domain doc. Load only what the task needs.
- Claude Code: path-scoped pointers in `.claude/rules/` auto-load when matching files are read.
- Codex: a PostToolUse hook injects the same domain pointers after file edits; skills load workflows on demand.
- After editing, `python3 scripts/check-doc-drift.py` mechanically lists which shared docs map to your diff — use it instead of guessing or loading everything.

## Cross-Agent Workflow

This project may be implemented, reviewed, continued, or closed by Claude Code or Codex in any order — one feature by one agent, the next feature or the review by the other.

- Role matters more than tool: an agent may be Implementer, Reviewer, Continuer, or Closer.
- Before continuing or reviewing work, inspect `git status`, the current diff, relevant code paths, and available verification output.
- When stopping mid-task or handing to the other agent, write `.agent/work/current.md` using `.agent/handoff-template.md`. Handoff notes explain intent and risk; they do not prove what is currently true.
- Private Claude memory and private Codex memory are not shared project truth. Shared durable facts belong in repository-visible files.

## Quality Contract

Done does not mean "code changed." Done means the affected loops are closed or explicitly marked unverified:

- Intent loop: the change solves the user's real request.
- Functional loop: entry, success path, failure/empty/loading states, and return path are reasonable.
- Logic loop: state transitions, related summaries, counters, filters, permissions, and side effects still make sense.
- UI/copy loop: visible behavior, layout, wording, and edge states are coherent.
- Data loop: persistence, migration, sync, backup, import/export, and deletion impacts are checked when touched.
- Verification loop: the final reply says exactly what was run or inspected, and what remains unverified.
- Drift loop: durable project facts changed by the work are updated in shared docs or called out.
- Rule-growth loop: `.agent/rule-candidates.md` has no ordinary `Status: pending` items before finalizing non-trivial work.

## Skills And Tools

- Skills are workflow loaders, not guarantees. Use automatic invocation when it triggers, but explicitly invoke or follow the relevant skill for high-risk work.
- MCP tools, CLIs, browser automation, device tools, database tools, and remote APIs are evidence sources. Use them when the task depends on live or private state.
- Durable rules stay in repository-visible `AGENTS.md` and `.agent/*`; skills, rules pointers, and MCP/tool integrations load or wrap those rules, not replace them.
- If a required tool is unavailable, say so. Do not infer live state from docs, memory, or another agent's summary.
- Before finalizing non-trivial changes: `python3 scripts/check-doc-drift.py` lists docs to review (advisory); `python3 scripts/suggest-rule-updates.py` writes candidates the agent must resolve autonomously.
- After installing Rules or large structure changes: `python3 scripts/bootstrap-project-context.py` refreshes the project map, command candidates, and bootstrap report.
- When changing the rules themselves, apply `.agent/rule-health.md`; prune or tighten noisy, stale, or over-specific rules.

## Risk Boundaries

Ask before actions that affect product direction, data safety, irreversible deletion, billing/pricing, external users, release, production remote state, or broad git history.

For ordinary implementation details, make the smallest reasonable decision that fits current code and the user's request, then explain it at the end.
