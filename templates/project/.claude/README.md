# Claude Code Local Config Templates

`settings.example.json` is an example only. Review it, then copy it to `.claude/settings.json` if you want Claude Code hook reminders.

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

The included Stop hook also runs `python3 scripts/check-doc-drift.py` when present.
