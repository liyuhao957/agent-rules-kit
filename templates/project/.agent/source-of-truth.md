# Source Of Truth

## Priority

1. Current user instruction.
2. Current code, config, tests, build results, tool output, git state, device state, and live remote state.
3. Shared project docs in `AGENTS.md`, `CLAUDE.md`, and `.agent/`.
4. README, issues, old handoffs, private memories, and historical summaries.

## Required Behavior

- Treat docs as routing and context, not final evidence.
- Verify any task-critical doc claim against current files, commands, tools, or remote state.
- If evidence conflicts, follow evidence and note the conflict when it mattered.
- Do not preserve stale implementation shape as a hard rule unless it is clearly marked as a safety constraint.
- Do not claim something was verified unless it was checked in the current turn.

