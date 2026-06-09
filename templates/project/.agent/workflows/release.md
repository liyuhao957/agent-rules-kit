# Workflow: Release Or External State

Use for publishing, deployment, app store work, production operations, pricing, billing, signing, remote config, or any external-state-changing task.

## Steps

1. Confirm scope if ambiguity affects users, money, data, irreversible state, or release target.
2. Inspect current repo and local changes.
3. Read relevant release/domain docs.
4. Verify auth, version, signing, environment, remote state, and target with real tools.
5. Use `.agent/command-contract.md` plus release docs to run required tests/builds/checks.
6. Make the smallest safe external change.
7. Verify the remote result with the same class of real tool.
8. Record exact evidence and remaining risk.

Do not infer release success from local logs, old docs, or another agent's summary.
