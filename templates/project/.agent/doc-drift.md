# Documentation Drift Rule

Update shared docs when a change modifies durable project behavior that future agents may rely on.

## Drift Discovery

Before finalizing non-trivial work, run:

```bash
python3 scripts/check-doc-drift.py
python3 scripts/suggest-rule-updates.py
```

Resolution protocol (statuses, real-notes requirement, archive): `.agent/index.md` (At Finalize). A candidate is a review signal, not proof that docs must change — decide from current evidence.

## How The Engine Behaves

- `check-doc-drift.py` reads `.agent/drift-map.yml` against current git changes and lists the shared docs mapped to your diff. The same globs drive on-demand loading (`.claude/rules/*.md` for Claude, the Codex PostToolUse router); when you change globs in the map, mirror them into `.claude/rules/*.md` frontmatter.
- After adaptation, the checker warns when a literal drift-map glob matches no repo file — the signal that the map went stale after a rename. Renames also fire the old path's rule once (`--no-renames`).
- Candidate ids are `<id>@<evidence-key>`; new evidence for the same rule resets the candidate to pending, with no status inheritance.
- Pending candidates are never dropped by regeneration; they carry forward until resolved. Committing does not clear them, and the Stop gate blocks on committed-but-pending items too.
- Resolved candidates move to a compact archive section in `.agent/rule-candidates.md` (the audit trail); rejected items stay suppressed. A status flipped to resolved without a real decision note reverts to pending on the next scan.
- Edits touching only `.agent/*` docs are auto-classified `checked-unchanged` ("rule-doc maintenance"), so promotions do not spawn review-the-review rounds.
- Vendor dirs (`node_modules`, `dist`, ...) never produce candidates.

## Update Docs When Changing

- Build, test, release, deploy, device, or local runtime workflow.
- Product identity, product principles, or core user journeys.
- Data model, persistence, sync, migration, backup, import/export, deletion, or privacy behavior.
- Localization, user-facing copy policy, or supported language behavior.
- Cross-agent handoff, review, verification, skills, hooks, or tool policy.
- Validation command inventory in `.agent/command-contract.md`.
- Rule scope, rule health, or drift-map behavior.
- Repeated pitfall that future agents are likely to hit again.

## Do Not Update Docs For

One-off implementation details, temporary experiments, facts easy to rediscover from code, speculation about future features, or cleanup that does not change durable behavior.

## If Docs Are Stale

If stale docs affected the task, fix them when in scope. If not in scope, mention the stale area in the final reply.

## Final Reply Expectation

For each drift signal say one of: updated, checked unchanged, out of scope, or not checked (with why). Do not leave `.agent/rule-candidates.md` with `Status: pending` for ordinary completed work.
