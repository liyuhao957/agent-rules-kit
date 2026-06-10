@AGENTS.md

# Claude Code Notes

- `AGENTS.md` is the shared project contract. If it did not load, stop and ask the user to verify Claude Code memory with `/memory`.
- If `.agent/adaptation-review.md` says `Status: pending`, follow `.agent/workflows/adapt-rules.md` before ordinary project work.
- Path-scoped pointers in `.claude/rules/` auto-load domain docs when you read matching files; `.agent/index.md` is the manual routing map. Load `.agent/*` docs on demand, not up front.
- Claude memory is private context, not shared project truth. If a fact, workflow, decision, pitfall, or verification rule should guide Codex too, write it into repository-visible docs under `.agent/`.
- Prefer the skills in `.claude/skills/` for task workflows; they route to the shared `.agent/` protocols so Claude and Codex stay aligned.
