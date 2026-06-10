# Domain: Release And External Operations

## Use When

Publishing, deploying, submitting to stores, changing production config, signing, credentials, pricing, billing, user-facing remote state, or irreversible external state.

## Verify Before Editing

- Current version/build/release identifiers.
- Authentication and permission status.
- Local dirty state and intended scope — do not sweep unrelated local changes into a release.
- Current remote state with authenticated tools; a runbook, skill, or memory is not proof of live state.
- Required tests/builds/checks from `.agent/command-contract.md`.

## Do

- Confirm scope when ambiguity affects users, money, data, or irreversible state.
- Verify remote state both before and after external changes, with the same class of real tool.
- Keep exact evidence for the final summary.

## Done Means

The external state change is verified with real output, or the task stops with the missing evidence clearly named.
