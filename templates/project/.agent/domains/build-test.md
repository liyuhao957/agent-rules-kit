# Domain: Build, Test, Device, Runtime

## Use When

Changing build setup, tests, local runtime, simulator/device flows, CI, scripts, generated project files, or developer commands.

## Verify Before Editing

- Current project files and scripts.
- Current available runtimes/devices/services.
- Existing test command patterns.
- Whether commands in docs are stale.
- `.agent/command-contract.md` for current command inventory.

## Do

- Prefer targeted validation first; broaden when risk is high.
- Report exact commands/checks run and their result.
- Update `.agent/command-contract.md` when a durable command changes.
- If a device or service is unavailable, separate environment failure from code failure.

## Do Not

- Claim a build/test/device path passed without current output.
- Update generated files manually when the project has a generator unless the workflow explicitly requires it.

## Done Means

The affected build/test/runtime path has current evidence, or the final reply clearly states what could not be verified.
