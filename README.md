# Claude Code + Codex Project Rules Kit

[English](./README.md) | [简体中文](./README.zh-CN.md)

A shared, plain-markdown contract so that whichever agent touches your project — Claude Code, Codex, or you — follows the same rules, verifies facts from the current code instead of stale docs, and finishes the whole job instead of half of it.

No runtime, no dependencies. Just markdown the agent reads, plus three small helper scripts. Built for the relay style of working: one feature by Claude, the next feature or the review by Codex, and back.

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

- `AGENTS.md` — the shared contract every agent reads first. Codex loads it natively at startup; Claude Code loads it through a thin `CLAUDE.md` that does `@AGENTS.md` (the officially documented bridge).
- `.agent/` — a set of short markdown files: product promises, user journeys, verified commands, per-domain rules, and a lifecycle routing index. Most start as templates the agent fills in from your real code.
- `.claude/rules/` — tiny path-scoped pointers (3 lines each) that auto-load the right domain doc the moment Claude reads a matching file.
- `.claude/skills/` — thin workflow loaders; the Codex tree under `.agents/skills/` is **generated from it at install time**, so the two tools can never drift apart.
- Hooks for both tools: a bash guard, a finalization gate, and (Codex only) a router that injects domain-doc pointers after edits.
- Three small Python scripts (standard library only, **no dependencies**) that scan the repo and **write suggestions**. They never edit your rules.

**The division of labor is the whole point: the agent is the judge; the scripts only collect evidence and flag what might be stale.** Nothing in here decides anything on its own.

It works with **one agent or two**, and from **commit zero**. See [Install](#install).

## On-demand loading (the token story)

Rules only help if they don't drown the agent. The kit keeps the always-loaded footprint to one small file and routes everything else on demand:

- **Always loaded:** `AGENTS.md` (~35 lines). That's the whole standing tax.
- **Loaded when files are touched:** Claude Code auto-loads a 3-line pointer from `.claude/rules/` when it reads a matching file (e.g. anything under `components/` points to `.agent/domains/ui-copy.md`). Codex, which has no path-scoped rules, gets the same pointer injected by a PostToolUse hook after an edit — once per area per session, one line each.
- **Loaded when invoked:** skills carry only their name and description until used; each routes to one shared workflow doc.
- **Listed mechanically:** after editing, `python3 scripts/check-doc-drift.py` prints exactly which shared docs map to the actual diff. The agent loads that list — not the whole `.agent/` directory.

So an ordinary task costs the contract, the domains it actually touched, plus a fixed finalize pass (the drift list and the candidate inbox — a couple of thousand tokens, independent of task size). The same glob map (`.agent/drift-map.yml`) drives routing and drift detection, and the globs are word-boundary precise: `ProductCard.tsx` does not trigger the production-risk rule, and a utility `.tsx` file outside UI directories does not nag about copy.

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

Two one-time steps after install: restart the agent session (so new skills are discovered), and approve the project hooks on first use — Claude Code asks about project settings; Codex needs the `.codex/` layer trusted and hooks reviewed via `/hooks`. **Until trusted, the hooks are inert.**

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

drift-map.yml                Globs tightened to this repo's real paths, then
  <default globs>            mirrored into .claude/rules/* frontmatter.
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

The scripts never promote anything themselves. You stay in control of what becomes a rule. The inbox is built so the lazy paths do not work:

- Candidates are keyed to their evidence (`drift:ui-copy@a1b2c3d`): a decision stays resolved for that evidence, but the same rule firing on **new** files resets to pending instead of inheriting last week's verdict.
- Pending items are never dropped by regeneration and survive commits — committing work does not clear the inbox, and the Stop gate blocks on committed-but-pending items too.
- A status flipped without a real decision note reverts to pending on the next scan.
- Resolved items move to a compact archive section (the audit trail), and a rejected candidate stays suppressed instead of coming back every run.
- Vendor output (`node_modules/`, `dist/`, …) and the kit's own installation files never produce candidates; the installer auto-resolves day-zero self-noise.

## What is actually enforced (and what isn't)

Honesty about enforcement matters more than the appearance of it. The exact split:

| Mechanism | Fires on | Blocks? |
| --- | --- | --- |
| Bash guard (PreToolUse, both tools) | force push, `git reset --hard`, `rm -rf` (except ephemeral dirs like `node_modules`/`dist`), release/deploy/publish/submit — including wrapped forms like `npx vercel deploy` and `sh -c "npm publish"` — production mutations, destructive SQL via remote-capable DB CLIs | **Yes** — exit 2; bypass `RULES_HOOK_ALLOW_RISK=1` |
| Finalization gate (Stop, both tools) | pending items in `.agent/rule-candidates.md` — from the current diff **or committed earlier**; committing is not a bypass | **Yes** — lists the pending IDs and the exact re-check command; the agent continues and resolves them (a Stop block means "keep going and fix this", not "halt"); bypass `RULES_HOOK_ALLOW_PENDING=1` |
| Doc-drift report | shown inside the gate's block message, and on demand | No — advisory list of docs to review |
| Stale-map warning | (post-adaptation) a literal drift-map glob matches no repo file — usually a renamed directory | No — one-line warning; the watcher's watcher |
| Domain router (PostToolUse, Codex) | first edit touching a mapped area | No — one-line pointer |
| Everything else — the quality loops, source-of-truth order, workflows | prose contract | No — agent judgment, by design |

So: the only hard gates are the narrow bash guard and the candidate inbox. "Don't trust stale docs" and "close every loop" are guidance the agent follows because the contract says so — the kit makes the right moment easy to catch, it does not prove correctness. Both hooks have a loop guard (`stop_hook_active`) so a gate can never spin forever.

## Install

The one command above (`agent-install-rules.sh --target <project>`) covers most cases. A few specifics:

**One agent only (Claude *or* Codex).** Install the normal way — the installer always writes both agents' files. Just use yours; the other set is inert unless that tool is running, and validation expects both to exist.

**Brand-new / empty repo.** Works from the first commit. The scan reports `none detected` and adaptation is light: the agent mostly confirms product intent with you and marks unknowns `needs-user`. Greenfield is the best time to install.

**Existing project that already has rules.** Add `--force`; old `AGENTS.md`, `CLAUDE.md`, `.agent/`, etc. are backed up under `.rules-kit/backups/` and read as clues during adaptation. If your old `.claude/settings.json` or `.codex/hooks.json` had custom hooks, permissions, or commands, the installer warns you and the adaptation workflow merges them back from the backup:

```bash
/path/to/agent-rules-kit/scripts/agent-install-rules.sh --target /path/to/project --force
```

**Updating the kit.** `--upgrade` replaces only kit machinery (scripts, hooks, skills, workflow docs) and never touches adapted content (`product-invariants.md`, `user-journeys.md`, `command-contract.md`, `drift-map.yml`, your active `settings.json`/`hooks.json`). Replaced files are backed up first:

```bash
/path/to/agent-rules-kit/scripts/agent-install-rules.sh --target /path/to/project --upgrade
```

**Removing the kit.** Delete the managed paths and restore anything you want from the oldest backup (later backups may contain a previous kit install, not your originals): `AGENTS.md`, `CLAUDE.md`, `.agent/`, `.agents/`, `.claude/`, `.codex/`, the three kit scripts under `scripts/` (`check-doc-drift.py`, `bootstrap-project-context.py`, `suggest-rule-updates.py` — other files in `scripts/` are yours), and finally `.rules-kit/`.

**Verify an install:**

```bash
# structure is in place:
/path/to/agent-rules-kit/scripts/validate-installed-project.sh /path/to/project
# the agent actually adapted it, not just installed it:
/path/to/agent-rules-kit/scripts/validate-installed-project.sh /path/to/project --require-adapted --require-candidates-reviewed
```

Validation checks **form, not correctness** — that status fields are filled, no template placeholders remain, the drift-map globs stay mirrored into `.claude/rules/*`, and candidates are resolved with real decision notes. It cannot judge whether the agent's facts are right; that is on the agent and you.

## Daily use, after adaptation

For ordinary work the agent reads `AGENTS.md`, routes through `.agent/index.md`, and loads only what the task needs — domain pointers arrive automatically when files are touched. It inspects the real code before editing, runs the verified commands from `.agent/command-contract.md`, and resolves the drift/candidate inbox before finishing non-trivial work.

For the dual-agent relay: when one agent stops mid-task, it writes `.agent/work/current.md` (objective, baseline commit, what's verified, what's not). The next agent — Claude or Codex — reconstructs state from `git status` and the diff, treating the note as intent, not proof.

When the rules themselves start to feel noisy or stale, `.agent/rule-health.md` is the guide for pruning, merging, or deleting them. The kit is meant to stay small, not grow into an encyclopedia.

## Philosophy

One idea underneath all of it: **the agent is the judge; the kit is the evidence collector.**

- Source-of-truth order: your current instruction → current code/config/tests/tools/live state → shared `.agent/` docs → READMEs, issues, old handoffs and memories.
- Private Claude or Codex memory is a personal hint, never shared project truth. Durable facts live in the repo where every agent can see them.
- Context is not enforcement (Anthropic's own framing): markdown guides the agent; the two narrow hooks block; tests and live tools prove.
- Skills, rules pointers, and MCP/tools are loaders and evidence channels, not the rule source. Durable rules stay in repo-visible markdown.
- A noisy detector feeding a blocking gate trains rubber-stamping — so detection is word-boundary precise and the advisory layer never blocks.

## Reference

<details>
<summary><strong>What gets installed (file map)</strong></summary>

```text
AGENTS.md                     shared contract; Codex reads it at startup, Claude via @import
CLAUDE.md                     thin Claude entrypoint, imports @AGENTS.md
.agent/
  index.md                    lifecycle routing map: load only what the task needs
  adaptation-review.md        Status: pending | adapted; plus needs-user items
  product-invariants.md       durable product promises
  user-journeys.md            main flows and the loops to close
  command-contract.md         verified commands (+ generated candidates)
  quality-gates.md            the loops that define "done"
  domains/*.md                ui-copy, data-sync, build-test, release, localization, performance
  workflows/*.md              adapt-rules, implement, review, continue, release
  drift-map.yml               changed paths → docs to review; also drives on-demand routing
  rule-candidates.md          script-written inbox; the agent resolves each item
  rule-health.md              when to prune, merge, or delete rules
.claude/
  rules/*.md                  path-scoped 3-line pointers; auto-load on matching file reads
  skills/*/SKILL.md           canonical thin workflow loaders (8)
  agents/*.md                 reviewer / qa / docs-drift-checker subagents
  hooks/*.py + settings.json  bash guard + finalization gate
.agents/skills/*              Codex skill tree — generated at install from .claude/skills
.codex/
  hooks/*.py + hooks.json     bash guard + finalization gate + domain router
scripts/*.py                  bootstrap-project-context, check-doc-drift, suggest-rule-updates
```

Recommended to commit: `AGENTS.md`, `CLAUDE.md`, `.agent/`, `.agents/`, `.claude/`, `.codex/`, `scripts/`. Keep `.agent/work/*` (handoff notes) local unless you intend to share them:

```gitignore
.agent/work/*
!.agent/work/README.md
```

</details>

<details>
<summary><strong>The full lifecycle: install → bootstrap → adapt → validate → grow</strong></summary>

1. **Install** — `agent-install-rules.sh` copies the templates, generates the Codex skill tree from the canonical Claude one, records metadata in `.agent/rules-kit.json`, backs up any existing rule files, and runs the bootstrap scan. The project is now *installed*, not *adapted*: `.agent/adaptation-review.md` still says `Status: pending`.
2. **Bootstrap** — `bootstrap-project-context.py` scans current files/config and writes **clues only** into `project-map.md`, `command-contract.md`, `bootstrap-report.md`, and `rule-candidates.md`. A file named `sync.ts` is a *signal*, not proof of verified cloud sync.
3. **Adapt** *(agent-driven)* — following `.agent/workflows/adapt-rules.md`, the agent inspects current code, config, tests, and any old backups, promotes **only verified facts** into `.agent/*`, tightens the drift-map globs to the project's real paths, and mirrors them into `.claude/rules/*`. Unprovable high-risk facts become `needs-user`.
4. **Validate** — `validate-installed-project.sh` checks that the structure exists, `CLAUDE.md` imports `@AGENTS.md`, the Codex skill tree matches the canonical one, scripts are executable, and (with the strict flags) that adaptation status and candidates are resolved. Form, not correctness.
5. **Grow** *(agent-driven)* — as code changes, the drift/candidate scripts surface possible stale docs; the agent promotes, checks-unchanged, rejects, or marks `needs-user`.

</details>
