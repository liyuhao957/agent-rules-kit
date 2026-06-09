# Tool And MCP Policy

Tools provide evidence. Use them when a task depends on live, private, generated, or environment-specific state.

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

