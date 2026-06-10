# Codex Local Config Templates

Rules installs `.codex/hooks.json` for you. `hooks.example.json` is kept as a reference copy.

Project-local layout:

```text
.codex/hooks.json                            active hook config
.codex/hooks/stop_quality_reminder.py        Stop gate: pending rule candidates
.codex/hooks/pre_bash_release_guard.py       PreToolUse guard: high-risk shell commands
.codex/hooks/post_edit_domain_router.py      PostToolUse router: injects .agent/domains/* pointers after edits
```

How loading works: Codex reads the repo `AGENTS.md` chain once at startup; skills under `.agents/skills/` load on demand (name + description up front, full text when selected); the PostToolUse router injects a one-line domain-doc pointer the first time an edit touches a mapped area — Codex has no path-scoped rules, so this hook fills that gap.

One-time setup after install:

- Codex loads project hooks only after you trust the project `.codex/` layer and review each hook via `/hooks`. Until then, the guards are inert.

By default, hooks block only narrow high-risk cases and otherwise stay quiet: force pushes, `git reset --hard`, `rm -rf`, release/deploy/publish/submit actions, production mutations, and finalizing non-trivial changes while `.agent/rule-candidates.md` still has pending candidates. The router and the doc-drift report are advisory and never block. Note: on a Stop-hook block, Codex does not halt — it continues with the hook's reason as a new continuation prompt, which is exactly the "resolve the pending candidates first" behavior the gate wants.

Use `RULES_HOOK_ALLOW_RISK=1` or `RULES_HOOK_ALLOW_PENDING=1` only for an intentional operation after explicit review.
