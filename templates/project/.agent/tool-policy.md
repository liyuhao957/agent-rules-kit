# Tool And MCP Policy

Tools provide evidence. Use them when a task depends on live, private, generated, or environment-specific state.

MCP servers and other tools may wrap repository scripts or expose live systems,
but they are evidence channels, not the durable rule source. Do not move core
project rules out of `AGENTS.md` or `.agent/*` just because a tool integration is
available.

## Use Tools For

- Current git state and diffs.
- Build, test, lint, typecheck, benchmark, and formatting evidence.
- Browser UI and screenshots.
- Simulator, device, emulator, or local runtime state.
- Database, analytics, logs, or internal system state.
- GitHub, issue tracker, CI, release, App Store, cloud, or production remote state.
- Current official documentation when the answer depends on recent or version-specific behavior.

## Do Not Infer Live State From

- Old docs.
- Private memory.
- Another agent's summary.
- Screenshots or logs from previous sessions.
- Unverified README instructions.

## If Tools Are Missing

Say which evidence could not be collected and why. Continue with the safest local verification available, or ask the user only when the missing evidence changes direction, safety, release, cost, or data risk.

## Hook Enforcement

Project hooks are mechanical guards around this repo-native contract.
Rules installs hook configs by default, but they should stay narrow enough to
avoid blocking ordinary exploration:

- Hooks block only narrow high-risk shell commands and non-trivial finalization with pending rule candidates.
- `RULES_HOOK_ALLOW_RISK=1` and `RULES_HOOK_ALLOW_PENDING=1` are escape hatches for intentional, reviewed operations.
- Hooks do not prove correctness; tests, builds, live tool output, and current code still provide the evidence.
