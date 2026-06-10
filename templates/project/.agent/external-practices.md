# External Practices Absorbed

This file records outside practices that shaped this rules kit. It is not a link dump; keep only ideas that affect how the template works.

## Adopted

- Short agent entrypoints: keep `AGENTS.md` and `CLAUDE.md` small, with deeper context loaded through task docs and skills.
- Progressive disclosure: use skills as workflow loaders, not as giant always-on prompts.
- Context is not enforcement: instructions and memory guide agents; hooks, tools, tests, and remote APIs provide stronger evidence.
- Shared repo truth: private agent memories are not shared across tools, so durable project facts live in repository-visible docs.
- Real-state verification: current code, tool output, build/test result, and live remote state outrank old docs.
- Drift discovery: use changed-path signals to decide which rules may need review instead of expecting users to remember.
- Rule health: rules themselves need pruning, moving, and verification over time.

## Not Adopted As Defaults

- Huge global rule files: they are easy to ignore and can crowd out task context.
- Fully automatic doc rewriting: too likely to create noisy or wrong docs; this kit detects candidates and asks agents to decide.
- Broad blocking hooks by default: project commands differ too much; installed hooks block only narrow high-risk cases and otherwise rely on agent judgment plus verification.
- Tool-specific private memory as project truth: Claude and Codex do not share private memory.

## Add More

When adopting a new outside practice, record:

- Source:
- Idea:
- What changed in this kit:
- Why it fits:
- What was deliberately not copied:
