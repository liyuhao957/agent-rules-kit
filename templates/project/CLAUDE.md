@AGENTS.md

# Claude Code Notes

- `AGENTS.md` is the shared project contract. If it did not load, stop and ask the user to verify Claude Code memory with `/memory`.
- If `.agent/adaptation-review.md` says `Status: pending`, follow `.agent/workflows/adapt-rules.md` before ordinary project work.
- Claude memory is private context, not shared project truth. Do not store durable project facts only in Claude memory.
- If a fact, workflow, decision, pitfall, or verification rule should guide Codex too, write it into repository-visible docs under `.agent/`.
- Prefer Claude Code skills in `.claude/skills/` for task workflows; they read the shared `.agent/` protocols so Claude and Codex stay aligned.
