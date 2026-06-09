---
name: release-safety
description: Use explicitly for release, publish, deploy, production, signing, billing, pricing, store, or external-state-changing tasks. Verify live state with real tools before and after.
---

# Release Safety

This skill should be explicitly invoked for high-risk external operations.

## Workflow

1. Read `.agent/workflows/release.md`.
2. Read `.agent/domains/release.md`.
3. Confirm scope if ambiguity affects users, money, data, irreversible state, or release target.
4. Verify local dirty state, auth, version, environment, and remote target with real tools.
5. Run required validation.
6. Make the smallest safe external change.
7. Verify remote result with real output.
8. Final reply must include exact evidence and remaining risk.

