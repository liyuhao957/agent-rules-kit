# Rule Health

Rules can rot. Review project rules when they become stale, too broad, too specific, contradictory, or ignored.

## Good Rules

- Apply across many future tasks.
- Tell agents how to verify facts, not only what to believe.
- Are short enough to load when needed.
- Have a clear owner file and trigger condition.
- Avoid encoding ordinary implementation details that code already reveals.

## Warning Signs

- A rule names files that no longer exist.
- Agents repeatedly ignore it because it is too vague.
- It duplicates another rule with slightly different wording.
- It turns current implementation shape into a permanent constraint.
- It causes noisy drift-check matches on unrelated changes.
- It describes a one-time incident as if it were a product invariant.

## Review Cadence

Run a rule-health review when:

- A new project installs this kit.
- `python3 scripts/bootstrap-project-context.py` is run for the first time.
- The kit is installed with `--force` and old rules were moved to `.rules-kit/backups/`.
- A large feature changes architecture, data flow, release flow, or core UI.
- Drift-check output is noisy more than twice for the same area.
- Claude and Codex behave differently because their instructions diverged.

## Review Output

For each issue, decide:

- Keep: still useful and accurate.
- Rewrite: useful but too vague or stale.
- Move: belongs in a domain doc, skill, hook, or command contract.
- Delete: no longer useful.
