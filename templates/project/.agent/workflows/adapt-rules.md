# Workflow: Adapt Rules To This Project

Use this workflow immediately after installing Rules into a new or existing project, and any time `.agent/adaptation-review.md` says `Status: pending`.

## Goal

Convert installed generic Rules into project-specific working rules by inspecting current evidence. Do not treat bootstrap output, old docs, memory, or another agent's summary as proof.

## Steps

1. Inspect the project root and git state.
2. Run or verify bootstrap output:

   ```bash
   python3 scripts/bootstrap-project-context.py
   ```

3. Read `.agent/bootstrap-report.md`, `.agent/project-map.md`, `.agent/command-contract.md`, `.agent/drift-map.yml`, and `.agent/adaptation-review.md`.
4. If `.rules-kit/backups/` exists, read old `AGENTS.md`, `CLAUDE.md`, and relevant old `.agent/*` files as clues only.
5. Inspect current code/config/docs for:
   - product purpose and durable product promises
   - main user journeys and UI/copy conventions
   - architecture, data lifecycle, sync/backup/import/export, destructive flows
   - build/test/runtime commands and generated project workflows
   - release/external-state workflows
   - localization and supported languages
   - tool, MCP, browser, device, database, or remote dependencies
6. Promote only verified, durable facts into:
   - `.agent/product-invariants.md`
   - `.agent/user-journeys.md`
   - `.agent/command-contract.md`
   - relevant `.agent/domains/*`
   - `.agent/drift-map.yml` — tighten the default globs to this project's real paths, then mirror them into `.claude/rules/*.md` frontmatter so Claude's auto-loading stays in step
7. Put unverified, risky, remote, credential, device, pricing, production, or release facts into `.agent/adaptation-review.md` under "Unverified / Needs User Confirmation".
8. Mark `.agent/adaptation-review.md`:
   - `Status: adapted`
   - `Adapted by: <agent/tool and date>`
   - check every completed evidence item
9. Run `python3 scripts/suggest-rule-updates.py` and handle every candidate in `.agent/rule-candidates.md` without asking the user unless the current task depends on an unprovable high-risk fact.
10. Run the validator from the rules-kit clone recorded in `.agent/rules-kit.json` (`source` field):

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
