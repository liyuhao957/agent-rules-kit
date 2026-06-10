# Codex Local Config Templates

Rules installs `.codex/hooks.json` for you. `hooks.example.json` is kept as a reference copy.

Suggested project-local layout:

```text
.codex/hooks.json
.codex/hooks/stop_quality_reminder.py
.codex/hooks/pre_bash_release_guard.py
```

Hooks are mechanical reminders and guards. They do not replace `.agent/quality-gates.md`, tools, tests, or careful review.

By default, hooks block only narrow high-risk cases and otherwise stay quiet: force pushes, `git reset --hard`, `rm -rf`, release/deploy/publish/submit actions, production mutations, and finalizing non-trivial changes while `.agent/rule-candidates.md` still has pending candidates.

Use `RULES_HOOK_ALLOW_RISK=1` or `RULES_HOOK_ALLOW_PENDING=1` only for an intentional operation after explicit review.
