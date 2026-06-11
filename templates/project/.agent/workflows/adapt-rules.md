# Workflow: Adapt Rules To This Project

Use this workflow immediately after installing Rules into a new or existing project, and any time `.agent/adaptation-review.md` says `Status: pending`.

## Goal

Convert installed generic Rules into project-specific working rules by inspecting current evidence. Do not treat bootstrap output, old docs, memory, or another agent's summary as proof.

## Minimum Honest Adaptation

MUST be done before marking `Status: adapted`:

- `.agent/command-contract.md`: every row verified by running or locating the command in the current repo.
- `.agent/drift-map.yml`: globs tightened to this project's real paths AND dead/unused default globs deleted; changes mirrored into `.claude/rules/*.md` frontmatter.
- `.agent/rule-candidates.md`: every candidate resolved with real decision notes.

`.agent/product-invariants.md` and `.agent/user-journeys.md` MAY be deferred when current code does not yet prove their content. Deferring is NOT leaving the template in place: replace the template body (the `Replace this template` / `project-specific` lines the validator flags) with a one-line `needs-user: <what is still unverified>` note, and record the same note under "Unverified / Needs User Confirmation" in `.agent/adaptation-review.md`. A deferred-and-noted file is handled, so its checklist box is ticked. Never tick a box for a file still carrying the raw template, and never leave the raw template behind — those are the only two dishonest moves here.

## Steps

1. Inspect the project root and git state.
2. Run or verify bootstrap output:

   ```bash
   python3 scripts/bootstrap-project-context.py
   ```

3. Read `.agent/bootstrap-report.md`, `.agent/project-map.md`, `.agent/command-contract.md`, `.agent/drift-map.yml`, and `.agent/adaptation-review.md`.
4. If `.rules-kit/backups/` exists, read old `AGENTS.md`, `CLAUDE.md`, and relevant old `.agent/*` files as clues only. If the backups contain a previous `.claude/settings.json` or custom hooks/commands, merge the user's entries back into the active config — the install must not silently drop them.
5. Inspect current code/config/docs for:
   - product purpose and durable product promises
   - main user journeys and UI/copy conventions
   - architecture, data lifecycle, sync/backup/import/export, destructive flows
   - build/test/runtime commands and generated project workflows
   - release/external-state workflows
   - localization and supported languages
   - tool, MCP, browser, device, database, or remote dependencies
6. Grep README and `docs/**` claims — endpoints, commands, paths, setup steps — against current code. Record every conflict in `.agent/adaptation-review.md` under "Unverified / Needs User Confirmation".
7. Promote only verified, durable facts into:
   - `.agent/product-invariants.md`
   - `.agent/user-journeys.md`
   - `.agent/command-contract.md`
   - relevant `.agent/domains/*`
   - `.agent/drift-map.yml` — tighten the default globs to this project's real paths, delete defaults that match nothing here, then mirror them into `.claude/rules/*.md` frontmatter so Claude's auto-loading stays in step
   - Prune domains this project does not have. The defaults are consumer-app shaped; a CLI/library/backend/ML repo usually has no `ui-copy`, `localization`, or `release`-to-store domain. For each dead domain, delete all three together: `.agent/domains/<name>.md`, `.claude/rules/<name>.md`, and its rule block in `.agent/drift-map.yml` (and drop its line from `.agent/index.md`). The validator accepts a pruned set; carrying dead domains is permanent noise.
8. Put unverified, risky, remote, credential, device, pricing, production, or release facts into `.agent/adaptation-review.md` under "Unverified / Needs User Confirmation".
9. Mark `.agent/adaptation-review.md`:
   - `Status: adapted`
   - `Adapted by: <agent/tool and date>`
   - check only the evidence items actually completed
10. Run `python3 scripts/suggest-rule-updates.py` and resolve every candidate per `.agent/index.md` (At Finalize), without asking the user unless the current task depends on an unprovable high-risk fact.
11. Run the validator from the rules-kit clone recorded in `.agent/rules-kit.json` (`source` field):

   ```bash
   bash <rules-kit-source>/scripts/validate-installed-project.sh . --require-adapted --require-candidates-reviewed
   python3 scripts/check-doc-drift.py
   ```

## Done Means

- Generic templates no longer pretend to be project-specific facts.
- Verified project facts are written into durable `.agent/*` docs.
- Unknown or high-risk facts are explicitly listed as unverified.
- Rule candidates are promoted, checked unchanged, rejected, or marked needs-user.
- Strict validation passes with `--require-adapted --require-candidates-reviewed`.
