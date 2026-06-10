# Claude Code Local Config Templates

Rules installs `.claude/settings.json` for you. `settings.example.json` is kept as a reference copy.

Suggested project-local layout:

```text
.claude/settings.json
.claude/hooks/stop_quality_reminder.py
.claude/hooks/pre_bash_release_guard.py
```

Claude Code also reads:

- `CLAUDE.md`
- `.claude/skills/*/SKILL.md`
- `.claude/agents/*.md`

Keep shared project truth in `.agent/`, not only in Claude memory.

By default, hooks block only narrow high-risk cases and otherwise stay quiet: force pushes, `git reset --hard`, `rm -rf`, release/deploy/publish/submit actions, production mutations, and finalizing non-trivial changes while `.agent/rule-candidates.md` still has pending candidates.

Use `RULES_HOOK_ALLOW_RISK=1` or `RULES_HOOK_ALLOW_PENDING=1` only for an intentional operation after explicit review.
