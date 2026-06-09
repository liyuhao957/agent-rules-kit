# Codex Local Config Templates

`hooks.example.json` is an example only. Review it, then copy it to `.codex/hooks.json` if you want hook reminders.

Suggested project-local layout:

```text
.codex/hooks.json
.codex/hooks/stop_quality_reminder.py
.codex/hooks/pre_bash_release_guard.py
```

Hooks are mechanical reminders and guards. They do not replace `.agent/quality-gates.md`, tools, tests, or careful review.

The included Stop hook also runs `python3 scripts/check-doc-drift.py` when present.
