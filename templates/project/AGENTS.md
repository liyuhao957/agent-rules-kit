# Project Agent Contract

This file is the shared project entrypoint for Codex, Claude Code through `CLAUDE.md`, and any coding agent that works in this repository.

## Read First

- For non-trivial work, read `.agent/index.md`, then only the workflow/domain docs relevant to the current task.
- If `.agent/adaptation-review.md` says `Status: pending`, run `.agent/workflows/adapt-rules.md` first. Installed templates and bootstrap candidates are not project rules until an agent has reviewed current code/config and marked adaptation complete.
- Project docs are navigation and context, not proof. Verify task-critical facts in current code, config, tool output, tests, builds, or live remote state before acting.
- Do not trust another agent's summary, handoff note, memory, or old report as proof. Use them as clues.
- Treat documented commands as examples until verified; use `.agent/command-contract.md` to find and maintain current validation commands.

## Source Of Truth

Priority order:

1. The user's current explicit instruction.
2. Current repository state, code, config, tests, build output, tool output, git state, device state, and live remote state.
3. Shared project docs under `.agent/`, `AGENTS.md`, and `CLAUDE.md`.
4. README files, issues, previous handoffs, memories, and old summaries.

If docs conflict with current evidence, follow current evidence, keep the change conservative, and mention the conflict if it affected the work.

## Cross-Agent Workflow

This project may be implemented, reviewed, continued, or closed by Claude Code or Codex in any order.

- Role matters more than tool: an agent may be Implementer, Reviewer, Continuer, or Closer.
- Before continuing or reviewing work, inspect `git status`, the current diff, relevant code paths, and available verification output.
- Handoff notes explain intent and risk; they do not prove what is currently true.
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
- Durable rules stay in repository-visible `AGENTS.md` and `.agent/*`; skills and MCP/tool integrations should load or wrap those rules, not replace them.
- If a required tool is unavailable, say so. Do not infer live state from docs, memory, or another agent's summary.
- Use `python3 scripts/check-doc-drift.py` before finalizing non-trivial changes to discover which shared docs may need review.
- Use `python3 scripts/suggest-rule-updates.py` before finalizing non-trivial changes; decide candidates autonomously and update `.agent/*` when current evidence supports it.
- Use `python3 scripts/bootstrap-project-context.py` after installing Rules or after large structure changes to refresh project-map, generated command candidates, drift candidates, and bootstrap-report.
- Use `.agent/rule-health.md` when changing the rules themselves; rules should be pruned or moved when they become noisy, stale, or too specific.

## Risk Boundaries

Ask before actions that affect product direction, data safety, irreversible deletion, billing/pricing, external users, release, production remote state, or broad git history.

For ordinary implementation details, make the smallest reasonable decision that fits current code and the user's request, then explain it at the end.
