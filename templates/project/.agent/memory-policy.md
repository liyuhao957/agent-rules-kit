# Memory Policy

Claude memory and Codex memory are private agent hints. They are not shared project truth.

Claude auto-memory lives per-machine under `~/.claude/projects/<project>/memory/`; Codex memories (experimental, off by default) live globally under `~/.codex/memories/`. Neither is visible to the other tool, another machine, or a teammate — which is exactly why durable facts belong in the repo.

## Use Private Memory For

- User interaction preferences.
- Agent-specific reminders.
- Repeated personal workflow hints.
- Search keywords that help rediscover prior evidence.

## Do Not Use Private Memory For

- Durable project rules.
- Build/test/release commands that both agents need.
- Product decisions that should guide future work.
- Data, sync, migration, deletion, privacy, billing, or release facts.
- Claims about current remote/device/tool state.

## Shared Memory Belongs In The Repo

If Claude and Codex both need to know it, put it in one of:

- `AGENTS.md`
- `CLAUDE.md`
- `.agent/*`
- `.agent/decisions/*`
- Code, tests, config, or scripts

Before relying on memory for project facts, verify against current evidence.

