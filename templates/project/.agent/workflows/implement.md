# Workflow: Implement

Use when adding or changing behavior.

## Steps

1. Restate the outcome and identify the affected user path.
2. Inspect `git status` and relevant current code/config; verify doc claims against current evidence before relying on them.
3. Load only the domain docs the task touches: route via `.agent/index.md`; after editing, `python3 scripts/check-doc-drift.py` lists the mapped docs for your actual diff.
4. Implement the smallest change that closes the requested loop; check related entry points, state transitions, UI/copy, data, and error paths.
5. Validate with commands from `.agent/command-contract.md` — targeted first, broader when risk or blast radius is high.
6. Finalize per `.agent/index.md` (At Finalize): quality gates, drift check, candidate scan, every pending candidate resolved with a real note.
7. Write `.agent/work/current.md` only if work remains or another agent needs context.

## Final Reply

Include what changed, what was verified, and what remains unverified.
