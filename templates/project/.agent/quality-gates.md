# Quality Gates

Use these gates before finalizing implementation, review, continuation, or release work.

## Intent Loop

- The objective matches the user's actual request, not only the nearest file-level change.
- Assumptions that affect product direction, safety, release, data, or cost were confirmed or explicitly called out.

## Functional Loop

- The user-facing entry point exists and is reachable.
- Main success path works by implementation, test, or direct inspection.
- Empty, loading, error, permission, cancellation, and retry states are handled when relevant.
- Navigation, return, refresh, and repeated-use paths remain reasonable.

## Logic Loop

- State transitions are consistent before and after the change.
- Related summaries, counts, filters, badges, notifications, cache, search, and derived views are not forgotten.
- Cross-module contracts and side effects are checked when touched.

## UI And Copy Loop

- Visible text sounds natural and product-appropriate.
- Layout handles realistic content, long text, empty state, and small/large viewport or device constraints when relevant.
- Interactive controls are reachable and communicate state clearly.

## Data Loop

- Persistence, schema, migration, sync, backup, import/export, deletion, undo, and recovery impacts are checked when touched.
- Destructive or irreversible paths require explicit user scope and verification.

## Verification Loop

- Run the smallest relevant validator that gives real evidence.
- Check `.agent/command-contract.md` for current validation commands, and verify commands still exist before relying on them.
- If full validation is not practical, run targeted checks and state the remaining risk.
- Final reply must distinguish run/inspected/inferred/unverified.

## Drift Loop

- If the change modifies durable project facts, update shared docs in the same task; if stale docs are out of scope, name the stale area and why.
- Run `python3 scripts/check-doc-drift.py` and report each signal as updated, checked unchanged, out of scope, or not checked (policy: `.agent/doc-drift.md`).

## Rule Growth Loop

- Resolve the candidate inbox before finalizing non-trivial work: protocol in `.agent/index.md` (At Finalize).
