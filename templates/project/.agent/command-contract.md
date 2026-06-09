# Command Contract

Commands in project docs are examples until verified in the current repo.

This file gives agents a single place to discover and update the project's current validation commands.

## Command Inventory

Fill or edit this section after installing the rules kit in a real project. This section is human/agent maintained; bootstrap does not overwrite it.

| Purpose | Command | Evidence Expected | Notes |
|---|---|---|---|
| Format | project-specific | exits 0 | optional |
| Lint | project-specific | exits 0 | optional |
| Typecheck | project-specific | exits 0 | optional |
| Unit tests | project-specific | exits 0 | targeted first |
| Build | project-specific | exits 0 | required before release |
| UI/runtime smoke | project-specific | visible path works | use browser/device when relevant |
| Release verification | project-specific | live tool confirms state | explicit high-risk workflow |

## Auto-Detected Command Candidates

Bootstrap refreshes only the block below. Promote a candidate into Command Inventory after verifying it.

# BEGIN GENERATED COMMAND CANDIDATES
- none detected
# END GENERATED COMMAND CANDIDATES

## Rules

- Before running a documented command for the first time in a task, verify it still exists.
- Prefer the smallest command that proves the affected behavior.
- If a command is missing or stale, inspect scripts/config to find the current one and update this file when the command is durable.
- Do not claim validation passed without current command output or tool evidence.
- For slow or unavailable commands, run the safest targeted alternative and state the remaining risk.
