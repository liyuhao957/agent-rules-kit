# Domain: Build, Test, Device, Runtime

## Use When

Changing build setup, tests, local runtime, simulator/device flows, CI, scripts, generated project files, or developer commands.

## Verify Before Editing

- Current project files, scripts, and available runtimes/devices/services.
- `.agent/command-contract.md` for the current command inventory; verify a documented command still exists before relying on it.

## Do

- Targeted validation first; broaden when risk is high. Report exact commands run and their results.
- Update `.agent/command-contract.md` when a durable command changes.
- Separate environment failure from code failure when a device or service is unavailable.
- Use the generator for generated files unless the workflow explicitly requires manual edits.

## Done Means

The affected build/test/runtime path has current evidence, or the final reply clearly states what could not be verified. No pass claims without current output.
