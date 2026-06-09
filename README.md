# Claude Code + Codex Project Rules Kit

[English](./README.md) | [简体中文](./README.zh-CN.md)

A shared, plain-markdown contract so that whichever agent touches your project — Claude Code, Codex, or you — follows the same rules, verifies facts from the current code instead of stale docs, and finishes the whole job instead of half of it.

No runtime, no dependencies. Just markdown the agent reads, plus three small helper scripts.

## The three traps it closes

Whether it's one agent across many sessions or a couple of them taking turns, the same three failures keep showing up on a real project.

**Trap 1 — Every fresh start reinvents how the project works.**
A new session opens the repo cold, with no reliable memory of earlier decisions, so it guesses at conventions, picks different names, and re-derives how things are done. It happens whether the next session is the same agent, the other agent, or you next month — two Claude sessions diverge as easily as Claude and Codex do. Multiply it over time and the codebase splinters.
*Fix:* write the durable decisions into one file in the repo that everyone reads first (`AGENTS.md`). Whoever picks up the work next starts from the same standard instead of guessing.
> Like a job site where nobody writes anything down: every crew — even the same one back next week — reinvents how the work gets done. Pin one "site handbook" to the wall and everyone builds the same way.

**Trap 2 — Trusting stale docs and building on the wrong thing.**
The doc says the login endpoint is `/api/login`, but the code moved to `/api/v2/auth` months ago. An agent that believes the doc writes against a target that no longer exists.
*Fix:* check the current code, config, and tests before acting. The real present state wins over old docs and memory.

**Trap 3 — Doing half the job, then calling it "done."**
The classic: it runs locally, nothing errors, ship it. But the data never saved, the page never showed it, the docs were never updated — and the actual user path is broken end to end.
*Fix:* a change isn't done until **feature, logic, data, UI, and docs** are wired together.

Take "add a `nickname` field to the user":

| Loop | Half done (the usual) | Closed loop (done) |
| --- | --- | --- |
| Feature | Input box added | Input box added |
| Logic | No save logic | Submitting actually persists it |
| Data | Column never added | Field added; reads and writes work |
| UI | Profile page ignores it | Shown everywhere it should be |
| Docs | API doc still old | Doc updated in step |

**In one line:** don't let every session freelance (one shared contract), don't trust stale docs (current code wins), and don't ship half a feature (UI → logic → data → docs all wired up).

## What it actually is

Be honest about the weight: this is **not a framework, an engine, or a runtime.** It's a folder of files you copy into your repo:

- `AGENTS.md` — the shared contract every agent reads first.
- `CLAUDE.md` — a thin Claude Code entrypoint that just imports `AGENTS.md`.
- `.agent/` — a set of short markdown files: product promises, user journeys, verified commands, per-domain rules, and the project's source-of-truth policy. Most start as templates the agent fills in from your real code.
- Skill and hook stubs for both Claude Code and Codex that point them at the shared `.agent/` rules.
- Three small Python scripts (standard library only, **no dependencies** — they even hand-roll their YAML parsing to avoid one) that scan the repo and **write suggestions**. They never edit your rules.

**The division of labor is the whole point: the agent is the judge; the scripts only collect evidence and flag what might be stale.** Nothing in here decides anything on its own.

It works with **one agent or two**, and from **commit zero** — you don't need both Claude and Codex, and you don't need an existing codebase. See [Install](#install).

## Quickstart

```bash
# 1. Clone the kit somewhere on your machine
git clone https://github.com/liyuhao957/agent-rules-kit.git

# 2. In your project, tell the agent (Claude Code or Codex):
#    "Install and adapt /path/to/agent-rules-kit for this project."
#    It runs:
/path/to/agent-rules-kit/scripts/agent-install-rules.sh --target /path/to/project
```

The installer copies the files and scans your repo for clues. Then the agent reads your actual code and **fills the templates in with verified facts** — that part is the agent's work, not the script's. From then on, any agent starts from `AGENTS.md` instead of rediscovering the project from scratch.

## What "adapted" looks like

Right after install, the rule files are generic templates and `.agent/adaptation-review.md` says `Status: pending`. The agent's job is to turn them into real, verified project facts. For example:

```text
Before (template)            After (agent filled in, verified from real code)
─────────────────            ───────────────────────────────────────────────
product-invariants.md        Free tier is capped at 3 projects.
  <durable promise>          Deleting an account purges synced data within 24h.

user-journeys.md             Sign up → verify email → create first project →
  <main flow>                land on dashboard.

command-contract.md          Test:  npm test       (ran it, passes)
  <verified command>         Build: npm run build  (ran it, succeeds)
```

Whatever the agent **can't** prove from code, tests, or tools — live billing state, production config, credentials — does not get promoted. It goes under `needs-user` in `.agent/adaptation-review.md` for you to confirm. Guessing is not allowed.

## How it stays honest as the code changes

This is the one mechanism that keeps the rules from rotting. After a non-trivial change, the agent runs:

```bash
python3 scripts/check-doc-drift.py       # reports which docs the change may have made stale
python3 scripts/suggest-rule-updates.py  # writes candidates into .agent/rule-candidates.md
```

Both scripts **only report and suggest.** The agent then resolves each candidate:

- `promoted` — verified true, written into the rules.
- `checked-unchanged` — looked, nothing to change.
- `rejected` — stale or too specific.
- `needs-user` — high-risk and unverifiable; ask the human.

The scripts never promote anything themselves. You stay in control of what becomes a rule.

## Install

The one command above (`agent-install-rules.sh --target <project>`) covers most cases. A few specifics:

**One agent only (Claude *or* Codex).** Install the normal way — there is no per-agent flag, and the installer always writes both agents' files. Just use yours; the other set is inert (it is never executed), and you should leave it in place because validation expects both to exist. Optionally wire up only your agent's hooks:

```bash
cp .claude/settings.example.json .claude/settings.json   # Claude
cp .codex/hooks.example.json     .codex/hooks.json       # Codex
```

Claude-only additionally gets subagents under `.claude/agents/` (reviewer, qa, docs-drift-checker); Codex-only keeps everything except those.

**Brand-new / empty repo.** Works from the first commit. The scan runs even with no code — it simply reports `none detected` and writes empty candidate lists. Adaptation is then light: the agent mostly confirms product intent with you and marks unknowns `needs-user`. Greenfield is the best time to install, since the rules grow with the project instead of being bolted on later.

**Existing project that already has rules.** Add `--force`; old `AGENTS.md`, `CLAUDE.md`, `.agent/`, etc. are backed up under `.rules-kit/backups/` and read as clues during adaptation:

```bash
/path/to/agent-rules-kit/scripts/agent-install-rules.sh --target /path/to/project --force
```

**Verify an install:**

```bash
# structure is in place:
/path/to/agent-rules-kit/scripts/validate-installed-project.sh /path/to/project
# the agent actually adapted it, not just installed it:
/path/to/agent-rules-kit/scripts/validate-installed-project.sh /path/to/project --require-adapted --require-candidates-reviewed
```

Validation checks **form, not correctness** — that status fields are filled and candidates resolved. It cannot judge whether the agent's facts are right; that is on the agent and you. The lower-level `install-rules.sh` (`--bootstrap`, `--force`, `--dry-run`, `--no-backup`) is there if you want to install without the agent wrapper.

## Daily use, after adaptation

For ordinary work the agent reads `AGENTS.md`, opens `.agent/index.md`, and loads only the workflow/domain docs the task needs — not every file every time. It inspects the real code before editing, runs the verified commands from `.agent/command-contract.md`, and runs the drift/candidate scripts before finishing non-trivial work.

When the rules themselves start to feel noisy or stale, `.agent/rule-health.md` is the guide for pruning, merging, or deleting them. The kit is meant to stay small, not grow into an encyclopedia.

## Philosophy

One idea underneath all of it: **the agent is the judge; the kit is the evidence collector.**

- Source-of-truth order: your current instruction → current code/config/tests/tools/live state → shared `.agent/` docs → READMEs, issues, old handoffs and memories.
- Private Claude or Codex memory is a personal hint, never shared project truth. Durable facts live in the repo where every agent can see them.
- Docs point the agent at the right checks; current code and real tool output are what actually prove a fact.
- Skills, hooks, and drift scripts make the right moment easier to catch — they do not replace judgment.

## Reference

<details>
<summary><strong>What gets installed (file map)</strong></summary>

```text
AGENTS.md                     shared contract, read first by every agent
CLAUDE.md                     thin Claude entrypoint, imports @AGENTS.md
.agent/
  index.md                    routes the agent to the right workflow/domain doc
  source-of-truth.md          what counts as proof; what must be re-checked
  adaptation-review.md        Status: pending | adapted; plus needs-user items
  product-invariants.md       durable product promises
  user-journeys.md            main flows and the loops to close
  command-contract.md         verified commands (+ generated candidates)
  domains/*.md                ui-copy, data-sync, build-test, release, localization, performance
  workflows/*.md              adapt-rules, implement, review, continue, release
  drift-map.yml               maps changed paths → docs that may need review
  rule-candidates.md          script-written inbox; the agent resolves each item
  rule-health.md              when to prune, merge, or delete rules
.agents/skills/*              Codex skill stubs that load the shared .agent rules
.claude/skills,agents,hooks   Claude Code equivalents (+ reviewer/qa/drift subagents)
.codex/hooks*                 Codex hook stubs + example config
scripts/*.py                  bootstrap-project-context, check-doc-drift, suggest-rule-updates
```

Recommended to commit: `AGENTS.md`, `CLAUDE.md`, `.agent/`, `.agents/`, `.codex/`, `scripts/`. Keep `.agent/work/*` (handoff notes) local unless you intend to share them:

```gitignore
.agent/work/*
!.agent/work/README.md
```

</details>

<details>
<summary><strong>The full lifecycle: install → bootstrap → adapt → validate → grow</strong></summary>

1. **Install** — `agent-install-rules.sh` copies the templates, records metadata in `.agent/rules-kit.json`, backs up any existing rule files (unless `--no-backup`), and runs the bootstrap scan. The project is now *installed*, not *adapted*: `.agent/adaptation-review.md` still says `Status: pending`.
2. **Bootstrap** — `bootstrap-project-context.py` scans current files/config and writes **clues only** into `project-map.md`, `command-contract.md`, `bootstrap-report.md`, and `rule-candidates.md`. A file named `sync.ts` is a *signal*, not proof of verified cloud sync.
3. **Adapt** *(agent-driven)* — following `.agent/workflows/adapt-rules.md`, the agent inspects current code, config, tests, and any old backups, then promotes **only verified facts** into `.agent/*`. Unprovable high-risk facts become `needs-user`.
4. **Validate** — `validate-installed-project.sh` checks that the structure exists, `CLAUDE.md` imports `@AGENTS.md`, scripts are executable, and (with `--require-adapted --require-candidates-reviewed`) that adaptation status and candidates are resolved. Form, not correctness.
5. **Grow** *(agent-driven)* — as code changes, the drift/candidate scripts surface possible stale docs; the agent promotes, checks-unchanged, rejects, or marks `needs-user`.

</details>

<details>
<summary><strong>Enabling hooks (optional)</strong></summary>

Hooks ship as examples so you opt in deliberately. They are reminders and guards — they do not replace validation. Review the commands first, then:

```bash
cp .codex/hooks.example.json     .codex/hooks.json        # Codex
cp .claude/settings.example.json .claude/settings.json    # Claude Code
```

The Stop hook also runs `python3 scripts/check-doc-drift.py` when present.

</details>
