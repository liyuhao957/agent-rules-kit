# Documentation Drift Rule

Update shared docs when a change modifies durable project behavior that future agents may rely on.

## Drift Discovery

Before finalizing non-trivial work, run:

```bash
python3 scripts/check-doc-drift.py
python3 scripts/suggest-rule-updates.py
```

The drift script reads `.agent/drift-map.yml`, checks current git changes, and reports which shared docs may need review. `suggest-rule-updates.py` writes those signals into `.agent/rule-candidates.md` along with command, backup, and high-risk candidates.

The same drift-map globs drive on-demand loading (`.claude/rules/*.md` for Claude, the Codex PostToolUse router for Codex). When you change globs in `.agent/drift-map.yml`, mirror them into `.claude/rules/*.md` frontmatter.

A candidate is a review signal, not proof that docs must change. The agent should decide autonomously from current evidence and mark each candidate `promoted`, `checked-unchanged`, `rejected`, or `needs-user`.

## Update Docs When Changing

- Build, test, release, deploy, device, or local runtime workflow.
- Product identity, product principles, or core user journeys.
- Data model, persistence, sync, migration, backup, import/export, deletion, or privacy behavior.
- Localization, user-facing copy policy, or supported language behavior.
- Cross-agent handoff, review, verification, skills, hooks, or tool policy.
- Validation command inventory in `.agent/command-contract.md`.
- Auto-generated context in `.agent/project-map.md` or `.agent/bootstrap-report.md`.
- Rule scope, rule health, or drift-map behavior.
- Repeated pitfall that future agents are likely to hit again.

## Do Not Update Docs For

- One-off implementation details.
- Temporary experiments.
- Obvious facts easy to rediscover from code.
- Speculation about future features.
- Cleanup that does not change durable behavior.

## If Docs Are Stale

If stale docs affected the task, fix them when in scope. If not in scope, mention the stale area in the final reply.

## Final Reply Expectation

When the drift check reports candidates, say one of:

- Updated: the relevant shared doc was changed.
- Checked unchanged: reviewed the suggested doc and it still applies.
- Out of scope: the signal was real but the doc update is not part of this task.
- Not checked: explain why the check could not be completed.

Do not leave `.agent/rule-candidates.md` with `Status: pending` for ordinary completed work.
