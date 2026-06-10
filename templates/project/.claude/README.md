# Claude Code Local Config Templates

Rules installs `.claude/settings.json` for you. `settings.example.json` is kept as a reference copy.

Project-local layout:

```text
.claude/settings.json                       active hook config
.claude/hooks/stop_quality_reminder.py      Stop gate: pending rule candidates
.claude/hooks/pre_bash_release_guard.py     PreToolUse guard: high-risk shell commands
.claude/rules/*.md                          path-scoped pointers -> .agent/domains/* (auto-load on file read)
.claude/skills/*/SKILL.md                   thin workflow loaders -> .agent/workflows/*
.claude/agents/*.md                         reviewer / qa / docs-drift-checker subagents
```

How loading works: `CLAUDE.md` imports `@AGENTS.md` at launch; everything else loads on demand — rules when you read matching files, skills when invoked, `.agent/*` docs when routed there. Keep shared project truth in `.agent/`, not only in Claude memory.

One-time setup after install:

- Claude Code asks you to approve project settings/hooks on first use; until approved, the hooks are inert.
- Restart the Claude Code session after install so new skills and subagents are discovered.

By default, hooks block only narrow high-risk cases and otherwise stay quiet: force pushes, `git reset --hard`, `rm -rf`, release/deploy/publish/submit actions, production mutations, and finalizing non-trivial changes while `.agent/rule-candidates.md` still has pending candidates. The doc-drift report is advisory and never blocks.

Use `RULES_HOOK_ALLOW_RISK=1` or `RULES_HOOK_ALLOW_PENDING=1` only for an intentional operation after explicit review.
