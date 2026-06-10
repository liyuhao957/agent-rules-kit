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
- Native path-scoped loading (Claude Code `.claude/rules/` with `paths:` frontmatter): domain pointers auto-load when matching files are read, instead of relying on the agent remembering to read them.
- Hook-injected routing for Codex (official PostToolUse `additionalContext`): Codex has no path-scoped rules and loads AGENTS.md only at startup, so a router hook injects domain pointers after edits, once per area per session.
- Script-computed doc lists (from github/spec-kit): the drift script tells the agent exactly which shared docs map to the current diff, instead of the agent loading everything or guessing.
- Recovery commands in gate errors (from github/spec-kit): when the Stop gate blocks, it lists pending candidate IDs and the exact command that verifies resolution.
- Stop-hook loop guard (`stop_hook_active`, official Claude/Codex hook contract): a Stop block asks the agent to act once; the guard prevents continuation loops.
- Word-boundary path matching: risk and classification signals use segmentized camelCase plus boundary regexes so `prod` does not match `ProductCard.tsx` — a noisy detector feeding a blocking gate trains rubber-stamping.

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
