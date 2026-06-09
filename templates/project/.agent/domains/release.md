# Domain: Release And External Operations

## Use When

Publishing, deploying, submitting to stores, changing production config, signing, credentials, pricing, billing, user-facing remote state, or irreversible external state.

## Verify Before Editing

- Current version/build/release identifiers.
- Authentication and permission status.
- Local dirty state and intended scope.
- Current remote state with authenticated tools.
- Required tests/builds/checks.
- `.agent/command-contract.md` for current build/test/release verification commands.

## Do

- Confirm scope when ambiguity affects users, money, data, or irreversible state.
- Verify both before and after external changes.
- Keep exact evidence for final summary.

## Do Not

- Treat a runbook, skill, or memory as proof of live state.
- Sweep unrelated local changes into a release.

## Done Means

The external state change is verified with real output, or the task stops with the missing evidence clearly named.
