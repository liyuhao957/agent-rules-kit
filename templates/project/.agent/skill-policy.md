# Skill Policy

Skills are workflow loaders. They increase the chance that the right process is used, but they are not a guarantee.

## Automatic Invocation

Allow automatic skill invocation for ordinary:

- implementation
- review
- continuation
- UI/copy checks
- quality gate checks
- documentation drift checks
- rule/doc drift discovery

## Explicit Invocation Required Or Strongly Preferred

Use explicit skill invocation or manually follow the skill for:

- release, publish, deploy, or production operations
- destructive data changes
- migration
- billing, pricing, subscription, or payment changes
- security-sensitive work
- auth, credentials, signing, certificates, or secrets
- external-state-changing operations

## Skill Design

- Keep skill descriptions precise and front-loaded with trigger words.
- Keep skill instructions short and point to shared `.agent/` docs.
- Do not duplicate long policy text separately for Claude and Codex.
- If a relevant skill fails to trigger automatically, invoke it manually or follow its referenced workflow.
- Skills should call shared scripts such as `python3 scripts/check-doc-drift.py` when a mechanical signal is more reliable than model judgment.
- Skills are adapters, not the rule source. Durable project rules stay in repository-visible `AGENTS.md` and `.agent/*` files so Claude, Codex, and humans can diff and review the same contract.
