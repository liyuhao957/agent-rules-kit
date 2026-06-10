# Relay Rules

[English](./README.md) | [简体中文](./README.zh-CN.md)

One set of rules for the agents working in your project — whether that's Claude Code alone or Claude and Codex taking turns: whoever picks up the work reads the same agreement first, trusts current code over stale docs, and finishes the whole job before stopping.

No runtime, no dependencies — just a folder of markdown files you copy into your repo, plus three small scripts. The "relay" in the name is first of all between sessions: with a single agent, today's session and next week's session are already a relay, and these rules are the baton. Two agents taking turns — one feature by Claude, the next feature or the review by Codex — is the two-runner version of the same thing.

## What it solves

Whether it's one agent across many sessions or two taking turns, the same three failures keep showing up on real projects.

**Trap 1 — Every fresh start reinvents how the project works.**
A new session opens the repo cold: no memory of earlier decisions, so it guesses at conventions, picks different names, and re-derives how things are done. It happens whether the next session is the same agent, the other agent, or you next month — two Claude sessions diverge as easily as Claude and Codex do. Multiply it over time and the codebase splinters.
*Fix:* write the durable decisions into one file in the repo that everyone reads first (`AGENTS.md`). Whoever picks up the work next starts from the same standard instead of guessing.
> Like a job site where nobody writes anything down: every crew — even the same one back next week — reinvents how the work gets done. Pin one "site handbook" to the wall and everyone builds the same way.

**Trap 2 — Trusting stale docs and building on the wrong thing.**
The doc says the login endpoint is `/api/login`, but the code moved to `/api/v2/auth` months ago. An agent that believes the doc writes against a target that no longer exists.
*Fix:* check the current code, config, and tests before acting. The real present state wins over old docs and memory.

**Trap 3 — Doing half the job, then calling it "done."**
The classic: it runs locally, nothing errors, ship it. But the data never saved, the page never showed it, the docs were never updated — and the path your user actually walks is broken end to end.
*Fix:* a change isn't done until **feature, logic, data, UI, and docs** are wired together.

Take "add a `nickname` field to the user":

| Loop | Half done (the usual) | Done (counts) |
| --- | --- | --- |
| Feature | Input box added | Input box added |
| Logic | No save logic | Submitting actually persists it |
| Data | Column never added | Field added; reads and writes work |
| UI | Profile page ignores it | Shown everywhere it should be |
| Docs | API doc still old | Doc updated in step |

In one line: don't let every session freelance (one shared agreement), don't trust stale docs (current code wins), and don't ship half a feature (everything wired up counts).

## How to use it

```bash
# 1. Clone the repo somewhere on your machine
git clone https://github.com/liyuhao957/relay-rules.git

# 2. In your project, tell the agent (Claude Code or Codex):
#    "Install and adapt /path/to/relay-rules for this project."
#    It runs:
/path/to/relay-rules/scripts/agent-install-rules.sh --target /path/to/project
```

Depending on your project's state, there are three ways to install:

- **First install** — the command above. You get templates plus a first clue-finding scan, waiting for the agent to adapt them (the "After install" section explains what adapting means). An empty repo works too — right at the start of a project is the best time to install. Using only one agent? That's the most common setup — install the same way; the files belonging to the other tool just sit there.
- **Your project already has its own `AGENTS.md` / `CLAUDE.md` / `.claude/`** — add `--force`. Your old files are backed up to `.rules-kit/backups/` before being replaced, and get read as clues during adaptation. If your old settings had custom hooks or permissions, the installer warns you and the adaptation workflow merges them back.
- **Installed before, new version out** — add `--upgrade`. Only the bundled scripts, hooks, skills, and workflow docs are updated; the project facts you filled in are not touched, and replaced files are backed up first. Structure the old install predates (like the `.claude/rules/` pointers) gets seeded automatically, with globs mirrored from your drift-map. If the new version added contract text to files you adapted, validation lists each missing piece at the end — have the agent merge those once from the template, then re-validate.

Two one-time steps after install (and after an upgrade): restart the agent session (so new skills are discovered), and approve the project hooks — Claude Code asks about project settings; if no prompt appears, check `/hooks`. Codex needs you to trust the project's `.codex/` directory and take a look at `/hooks`. **Until approved, the hooks do nothing.**

To confirm the install:

```bash
# structure is in place:
/path/to/relay-rules/scripts/validate-installed-project.sh /path/to/project
# the agent actually adapted it, not just installed it:
/path/to/relay-rules/scripts/validate-installed-project.sh /path/to/project --require-adapted --require-candidates-reviewed
```

Validation checks **form, not correctness** — fields filled, template placeholders gone, every decision carrying a real reason. Whether the facts themselves are right is on the agent and you.

**Uninstall**: delete what the installer wrote — `AGENTS.md`, `CLAUDE.md`, `.agent/`, `.agents/`, `.claude/`, `.codex/`, the three scripts under `scripts/` (`check-doc-drift.py`, `bootstrap-project-context.py`, `suggest-rule-updates.py`; everything else in `scripts/` is yours), and finally `.rules-kit/`. Restore anything you want from the oldest backup (later backups may contain a previous install, not your originals).

## What it actually is

Be honest about the weight: this is **not a framework, an engine, or a runtime.** It's a folder of files copied into your repo:

- `AGENTS.md` — the shared agreement everyone reads first. Codex loads it natively at startup; Claude Code loads it through a thin `CLAUDE.md` that does `@AGENTS.md` (the officially documented bridge).
- `.agent/` — a set of short markdown files: product promises, user journeys, verified commands, per-domain rules, and an index of which doc to read for which task. Most start as templates the agent fills in from your real code.
- `.claude/rules/` — tiny pointer files (a one-line note plus path-matching rules): the moment Claude reads a matching file, the right domain doc auto-loads.
- `.claude/skills/` — thin workflow entries; the Codex tree under `.agents/skills/` is generated from it at install time, so the two sides can never diverge.
- Hooks for both tools. The bash guard blocks dangerous commands; the Stop gate guards finishing — work can't end while the inbox still holds unhandled "candidates" (explained below); Codex additionally gets a domain router that delivers the same pointers after edits.
- Three small Python scripts (standard library only, zero dependencies) that scan the repo and write suggestions. They never edit your rules directly.

The division of labor is the whole point: **the agent is the judge; the scripts only collect evidence and flag what might be stale.** Nothing in here decides anything on its own.

## After install: adapt → daily use → staying fresh

**Adapting just means filling the templates with your project's truth.** Right after install, `.agent/adaptation-review.md` says `Status: pending`; the agent's job is to read your real code and turn generic templates into verified project facts:

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

Whatever the agent **can't** prove from code, tests, or tools — live billing state, production config, credentials — never gets written into the rules. It's marked `needs-user` for you to confirm. Guessing is not allowed.

**Daily use needs nothing from you.** The agent reads `AGENTS.md` and loads only the docs this task needs, via the index — touch an area and that domain's pointer arrives on its own. It inspects real code before editing and runs the verified commands from `.agent/command-contract.md`. When stopping mid-task — whether the next runner is its own next session or the other agent — it writes a handoff note (`.agent/work/current.md`: objective, baseline commit, what's verified, what's not); whoever picks up rebuilds the scene from `git status` and the diff — the note is a reference, not evidence.

**Staying fresh runs through one inbox.** This is the mechanism that keeps the rules from rotting. After any non-trivial change, the agent runs two scripts:

```bash
python3 scripts/check-doc-drift.py       # lists which docs this change may have made stale
python3 scripts/suggest-rule-updates.py  # writes "candidates" into the inbox (.agent/rule-candidates.md)
```

**A candidate is a to-do note the scripts write for the agent**: "this part of the code changed; some rule may now be stale — go look, and decide." The scripts only remind, never edit rules; the agent works through each one, choosing from four outcomes:

- `promoted` — verified true, written into the rules;
- `checked-unchanged` — looked, nothing to change;
- `rejected` — not worth being a rule;
- `needs-user` — can't verify (e.g. live state); left for you.

The inbox is built so it can't be brushed off:

- Every candidate is tied to the exact files that triggered it (the `@a1b2c3d` suffix in `drift:ui-copy@a1b2c3d`). The same rule firing on **new** files later creates a fresh to-do instead of reusing last week's verdict.
- Unhandled candidates don't disappear when code is committed — committing is not resolving, and the Stop gate still blocks.
- Flipping a status without writing a real reason doesn't count — the next scan reverts it.
- Handled items move to an archive at the bottom of the file, so the history stays readable; a rejected one won't keep coming back.
- Dependency and build output (`node_modules/`, `dist/`, …) never produces candidates, and the installer handles the candidates its own files trigger — a fresh install starts with a clean inbox.

When the rules themselves start to feel noisy or stale, `.agent/rule-health.md` is the guide for pruning, merging, or deleting. This is meant to stay small, not grow into an encyclopedia.

## What actually blocks (and what doesn't)

Honesty about enforcement matters more than the appearance of it. The exact split:

| Mechanism | Fires on | Blocks? |
| --- | --- | --- |
| Bash guard (PreToolUse, both tools) | force push; `git reset --hard`; `rm -rf` (with an exception for rebuildable dirs like `node_modules` and `dist`); release/deploy/publish/submit commands, including wrapped forms like `npx vercel deploy` and `sh -c "npm publish"`; commands that change production state; destructive SQL through a real database CLI (`psql`, `mysql`) | **Yes** — exit 2; bypass `RULES_HOOK_ALLOW_RISK=1` |
| Stop gate (both tools) | unhandled candidates in the inbox, whether from the current diff or committed earlier | **Yes** — lists the pending IDs and the exact re-check command; the agent continues and resolves them (a Stop block means "keep going and fix this", not "halt"); bypass `RULES_HOOK_ALLOW_PENDING=1` |
| Doc-drift report | on demand; also shown whenever the Stop gate blocks | No — advisory list of docs to review |
| Drift-map self-check | after adaptation, a concrete path in the map matches no file in the repo — usually a renamed directory | No — one-line warning that the map itself went stale |
| Codex domain router (PostToolUse) | first edit touching a mapped area | No — one-line pointer |
| Everything else — the quality loops, source-of-truth order, workflows | the written agreement | No — agent judgment, by design |

So: only two things ever block — the narrow bash guard and the Stop gate. "Don't trust stale docs" and "finish the whole job" hold because the agent keeps the agreement — the rules make the right moment easy to catch, they don't prove correctness. The Stop gate carries an anti-loop switch (`stop_hook_active`), so it can never block forever.

## The token story

Rules that flood the context hurt more than they help. So:

- **Always loaded: one ~35-line `AGENTS.md`.** That's the entire fixed cost.
- Domain docs **load only when their files are touched**: Claude via the tiny pointers that auto-load on read, Codex via the same pointer injected after an edit (once per area per session).
- Skills **expand only when invoked**; at the end of a task the scripts **mechanically list** which docs map to the actual diff, and the agent reads that list — not the whole directory.

An ordinary task costs the agreement itself, the domains it actually touched, plus a fixed end-of-task check (the doc-drift report and the inbox — a couple of thousand tokens regardless of task size). Matching is word-boundary precise: `ProductCard.tsx` won't trip the production rule just for containing "prod", and a utility file outside UI directories won't get nagged about copy.

## Philosophy

One idea underneath all of it: **the agent is the judge; the rules are the evidence collector.**

- Source-of-truth order: your current instruction → current code/config/tests/tools/live state → shared docs in the repo → READMEs, issues, old handoffs and memories.
- Private Claude or Codex memory is a personal cheat sheet, never shared truth. Anything both sides must follow goes into a file in the repo that everyone can see.
- Words guide, the two narrow hooks block, tests and real tools prove — three different jobs, never confused (context is not enforcement, as Anthropic itself puts it).
- A noisy detector feeding a blocking gate teaches the agent to rubber-stamp — so detection stays precise (word-boundary level), and warnings and reports never block anyone.

## Reference

<details>
<summary><strong>What gets installed (file map)</strong></summary>

```text
AGENTS.md                     shared agreement; Codex reads it at startup, Claude via @import
CLAUDE.md                     thin Claude entrypoint, imports @AGENTS.md
.agent/
  index.md                    the index: load only what the task needs
  adaptation-review.md        Status: pending | adapted; plus needs-user items
  product-invariants.md       durable product promises
  user-journeys.md            main flows and the loops to close
  command-contract.md         verified commands (+ generated candidates)
  quality-gates.md            the loops that define "done"
  domains/*.md                ui-copy, data-sync, build-test, release, localization, performance
  workflows/*.md              adapt-rules, implement, review, continue, release
  drift-map.yml               changed paths → docs to review; also drives on-demand loading
  rule-candidates.md          the candidate inbox: scripts write, the agent decides
  rule-health.md              when to prune, merge, or delete rules
  project-map.md etc.         bootstrap-scan output (with bootstrap-report.md; clues only)
  handoff-template.md, work/  the handoff note template and where notes live
  decisions/                  durable decisions worth leaving for whoever comes next
  doc-drift.md, *-policy.md   mechanism and policy docs, read on demand
.claude/
  rules/*.md                  path pointers; auto-load on matching file reads
  skills/*/SKILL.md           thin workflow entries (8; the Codex tree is generated from this side)
  agents/*.md                 reviewer / qa / docs-drift-checker subagents
  hooks/*.py + settings.json  bash guard + Stop gate
.agents/skills/*              Codex skill tree — generated at install from .claude/skills
.codex/
  hooks/*.py + hooks.json     bash guard + Stop gate + domain router
scripts/*.py                  bootstrap-project-context, check-doc-drift, suggest-rule-updates
```

Recommended to commit: `AGENTS.md`, `CLAUDE.md`, `.agent/`, `.agents/`, `.claude/`, `.codex/`, `scripts/`. Keep `.agent/work/*` (handoff notes) local unless you intend to share them:

```gitignore
.agent/work/*
!.agent/work/README.md
```

</details>

<details>
<summary><strong>The full lifecycle: install → bootstrap scan → adapt → validate → grow</strong></summary>

1. **Install** — `agent-install-rules.sh` copies the templates, generates the Codex skill tree from the canonical Claude one, records metadata in `.agent/rules-kit.json`, backs up any existing rule files, and runs the bootstrap scan. The project is now *installed*, not *adapted*: `.agent/adaptation-review.md` still says `Status: pending`.
2. **Bootstrap scan** — `bootstrap-project-context.py` scans current files/config and writes **clues only** into `project-map.md`, `command-contract.md`, `bootstrap-report.md`, and `rule-candidates.md`. A file named `sync.ts` is a *signal*, not proof of verified cloud sync.
3. **Adapt** *(agent-driven)* — following `.agent/workflows/adapt-rules.md`, the agent inspects current code, config, tests, and any old backups, writes **only verified facts** into `.agent/*`, tightens the drift-map globs to the project's real paths, and mirrors them into `.claude/rules/*`. Unprovable high-risk facts become `needs-user`.
4. **Validate** — `validate-installed-project.sh` checks that the structure exists, `CLAUDE.md` imports `@AGENTS.md`, the Codex skill tree matches the canonical one, scripts are executable, and (with the strict flags) that adaptation status, placeholders, and candidates are all handled. Form, not correctness.
5. **Grow** *(agent-driven)* — as code changes, the two scan scripts surface possibly stale docs and new candidates; the agent verifies, confirms unchanged, rejects, or marks `needs-user`.

</details>
