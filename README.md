# Relay Rules

[English](./README.md) | [简体中文](./README.zh-CN.md)

**One set of rules every agent in your repo reads first — so the next session picks up where the last one left off, instead of starting over.**

It's a folder of markdown files plus a few small scripts you copy into your project. No runtime, no dependencies. Works with Claude Code alone, or with Claude and Codex taking turns: whoever picks up the work reads the same agreement, trusts current code over stale docs, and finishes the whole job before stopping.

The "relay" starts with a single agent. Today's session and next week's session are already a relay — these rules are the baton. Two agents taking turns is just the two-runner version.

## The three failures it fixes

**1. Every fresh session reinvents how the project works.**
A new session opens the repo cold: it guesses at conventions, picks different names, re-derives decisions that were already made. Two Claude sessions diverge as easily as Claude and Codex do, and over time the codebase splinters.
→ Durable decisions go into one file everyone reads first: `AGENTS.md`. Whoever comes next starts from the same standard instead of guessing.

**2. Stale docs get trusted over real code.**
The doc says the login endpoint is `/api/login`; the code moved to `/api/v2/auth` months ago. An agent that believes the doc builds against a target that no longer exists.
→ Current code, config, and tests win over old docs and memory. Check first, then act.

**3. Half the job ships as "done".**
It runs locally, nothing errors — but the data never saved, the page never showed it, the docs never changed. Take "add a `nickname` field to the user":

| Step | Half done (the usual) | Done (counts) |
| --- | --- | --- |
| Feature | Input box added | Input box added |
| Logic | No save logic | Submitting actually persists it |
| Data | Column never added | Field added; reads and writes work |
| UI | Profile page ignores it | Shown everywhere it should be |
| Docs | API doc still old | Doc updated in step |

→ A change is done when feature, logic, data, UI, and docs are all wired together.

In one line: one shared agreement, current code wins, everything wired up counts.

## Who it's for

- **One agent across many sessions** — the most common setup. The files for the other tool just sit there, doing no harm.
- **Claude and Codex taking turns** — one feature by Claude, the next (or the review) by Codex, both on the same agreement.
- **Any project stage, including an empty repo** — right at the start is the best time to install.

## Install

```bash
# 1. Clone this repo anywhere on your machine
git clone https://github.com/liyuhao957/relay-rules.git

# 2. In your project, tell your agent (Claude Code or Codex):
#    "Install and adapt /path/to/relay-rules for this project."
#    It runs:
/path/to/relay-rules/scripts/agent-install-rules.sh --target /path/to/project
```

Three situations:

- **First install** — the command above. You get templates plus a first clue-finding scan; the agent adapts them next (see [After install](#after-install-adapt--daily-use--staying-fresh)).
- **Your project already has its own `AGENTS.md` / `CLAUDE.md` / `.claude/`** — add `--force`. Old files are backed up to `.rules-kit/backups/` before being replaced, then read as clues during adaptation. If your old settings had custom hooks or permissions, the installer warns you, and the adaptation workflow merges them back from the backup.
- **Installed before, new version out** — add `--upgrade`. Only the kit's own machinery is updated — bundled scripts, hooks, skills, workflow docs, the `.agent/index.md` index, and the example configs; the project facts you filled in are not touched, and replaced files are backed up first. If the new version added contract text to files you adapted, validation lists each missing piece at the end — have the agent merge those once from the template, then re-validate.

**Two one-time steps after install (and after every upgrade):**

1. Restart the agent session, so new skills are discovered.
2. Approve the project hooks — Claude Code asks about project settings (if no prompt appears, check `/hooks`); Codex needs you to trust the project's `.codex/` directory and review `/hooks`. **Until approved, the hooks do nothing.**

To confirm the install:

```bash
# structure is in place:
/path/to/relay-rules/scripts/validate-installed-project.sh /path/to/project
# the agent actually adapted it, not just installed it:
/path/to/relay-rules/scripts/validate-installed-project.sh /path/to/project --require-adapted --require-candidates-reviewed
```

Validation checks **form, not correctness** — fields filled, template placeholders gone, every decision carrying a real reason. Whether the facts themselves are right is on the agent and you.

## Uninstall

One command, fully lossless — nothing is deleted, only moved:

```bash
/path/to/relay-rules/scripts/uninstall-rules.sh --target /path/to/project   # add --dry-run to preview
```

It moves every kit-managed path into `.rules-kit/backups/rules-uninstall-<timestamp>/`, restores the files you had before the first install, and lists every backed-up file that carries your content (adapted project facts, your own files inside kit directories) so you can copy back what you still need. Once satisfied, delete `.rules-kit/` yourself to finish. (If the project is a git repo with a pre-install commit, a git rollback is always the cleanest uninstall — this script covers the other cases.)

## What gets installed

Not a framework, not an engine, no runtime — just files:

- `AGENTS.md` — the shared agreement, ~35 lines. Codex loads it natively at startup; Claude Code imports it through a thin `CLAUDE.md` that does `@AGENTS.md` (the officially documented bridge).
- `.agent/` — short markdown docs: product promises, user journeys, verified commands, per-domain rules, and an index of which doc to read for which task. Most start as templates the agent fills in from your real code.
- `.claude/rules/` — tiny pointer files: the moment Claude reads a matching file, the right domain doc auto-loads.
- `.claude/skills/` — thin workflow entries; the Codex tree under `.agents/skills/` is generated from it at install time, so the two sides can never diverge.
- Hooks for both tools — a bash guard that blocks dangerous commands, and a Stop gate that blocks finishing while the inbox still holds unhandled "candidates" (explained below). Codex additionally gets a domain router that delivers the same pointers after edits.
- Three small Python scripts (standard library only, zero dependencies) that scan the repo and write suggestions — into the inbox and clearly marked generated blocks, never over what you or the agent wrote.

The division of labor is the whole point: **the agent is the judge; the scripts only collect evidence and flag what might be stale.** Nothing in here decides anything on its own.

## After install: adapt → daily use → staying fresh

**Adapting means filling the templates with your project's verified truth.** Right after install, `.agent/adaptation-review.md` says `Status: pending`; the agent's job is to read your real code and turn generic templates into verified facts:

```text
Before (template)            After (agent filled in, verified from real code)
─────────────────            ───────────────────────────────────────────────
product-invariants.md        Free tier is capped at 3 projects.
  <durable promise>          Deleting an account purges synced data within 24h.

user-journeys.md             Sign up → verify email → create first project →
  <main flow>                land on dashboard.

command-contract.md          Test:  npm test       (ran it, passes)
  <verified command>         Build: npm run build  (ran it, succeeds)

drift-map.yml                The "changed paths → docs to review" map,
  <default globs>            tightened to this repo's real paths.
```

Whatever the agent **can't** prove from code, tests, or tools — live billing state, production config, credentials — never gets written into the rules. It's marked `needs-user` for you to confirm. Guessing is not allowed.

**Daily use needs nothing from you.** The agent reads `AGENTS.md` and loads only the docs this task needs — touch a UI file and the UI rules arrive on their own; nothing else loads. It inspects real code before editing and runs the verified commands from `.agent/command-contract.md`. When stopping mid-task, it writes a handoff note (`.agent/work/current.md`: objective, baseline commit, what's verified, what's not); whoever picks up rebuilds the scene from `git status` and the diff — the note is a reference, not evidence.

**Staying fresh runs through one inbox.** This is what keeps the rules from rotting. After any non-trivial change, the agent runs two scripts:

```bash
python3 scripts/check-doc-drift.py       # lists which docs this change may have made stale
python3 scripts/suggest-rule-updates.py  # writes "candidates" into the inbox (.agent/rule-candidates.md)
```

**A candidate is a to-do note the scripts write for the agent**: "this part of the code changed; some rule may now be stale — go look, and decide." The scripts only remind, never edit; the agent works through each one, choosing from four outcomes: `promoted` (verified, written into the rules), `checked-unchanged` (looked, nothing to change), `rejected` (not worth being a rule), or `needs-user` (can't verify; left for you).

The inbox is built so it can't be brushed off:

- Every candidate is tied to the exact files that triggered it (the `@a1b2c3d` suffix in `drift:ui-copy@a1b2c3d`). The same rule firing on **new** files later creates a fresh to-do instead of reusing last week's verdict.
- Committing is not resolving — unhandled candidates survive the commit, and the Stop gate still blocks.
- Flipping a status without writing a real reason doesn't count; the next scan reverts it.
- Handled items move to an archive at the bottom of the file — history stays readable, and a rejected one won't keep coming back.
- Dependency and build output (`node_modules/`, `dist/`, …) never produces candidates, and the installer resolves the ones its own files trigger — what a fresh inbox holds is only what the scan found in *your* project (detected commands, old backups), for the adaptation pass to verify.

When the rules themselves start to feel noisy or stale, `.agent/rule-health.md` is the guide for pruning, merging, or deleting. This is meant to stay small, not grow into an encyclopedia.

## What actually blocks (and what doesn't)

Honesty about enforcement matters more than the appearance of it. The exact split:

| Mechanism | Fires on | Blocks? |
| --- | --- | --- |
| Bash guard (PreToolUse, both tools) | force push; `git reset --hard`; `rm -rf` (except rebuildable dirs like `node_modules`, `dist`); release/deploy/publish/submit commands, including wrapped forms like `npx vercel deploy` and `sh -c "npm publish"`; commands that change production state; destructive SQL through a real database CLI (`psql`, `mysql`) | **Yes** — exit 2; bypass `RULES_HOOK_ALLOW_RISK=1` |
| Stop gate (both tools) | unhandled candidates in the inbox, whether from the current diff or committed earlier | **Yes** — lists the pending IDs and the re-check command; a Stop block means "keep going and fix this", not "halt"; bypass `RULES_HOOK_ALLOW_PENDING=1` |
| Doc-drift report | on demand; also shown when the Stop gate blocks on current changes | No — advisory list of docs to review |
| Drift-map self-check | after adaptation, a path in the map matches no file in the repo — usually a renamed directory | No — one-line warning that the map itself went stale |
| Codex domain router (PostToolUse) | first edit touching a mapped area | No — one-line pointer |
| Everything else — quality loops, source-of-truth order, workflows | the written agreement | No — agent judgment, by design |

So only two things ever block: the narrow bash guard and the Stop gate. "Don't trust stale docs" and "finish the whole job" hold because the agent keeps the agreement — the rules make the right moment easy to catch; they don't prove correctness. The Stop gate carries an anti-loop switch (`stop_hook_active`), so it can never block forever.

## The token cost

Rules that flood the context hurt more than they help. So:

- **Always loaded: one ~35-line `AGENTS.md`.** That's the entire fixed cost.
- Domain docs load **only when their files are touched** — Claude via pointers that auto-load on read, Codex via the same pointer injected after an edit (once per area per session).
- Skills expand **only when invoked**; at the end of a task the scripts mechanically list which docs map to the actual diff, and the agent reads that list — not the whole directory.

An ordinary task costs the agreement itself, the domains it actually touched, plus a fixed end-of-task check (a couple of thousand tokens regardless of task size). Matching is word-boundary precise: `ProductCard.tsx` won't trip the production rule just for containing "prod".

## Philosophy

One idea underneath all of it: **the agent is the judge; the rules are the evidence collector.**

- Source-of-truth order: your current instruction → current code/config/tests/tools/live state → shared docs in the repo → READMEs, issues, old handoffs and memories.
- Private Claude or Codex memory is a personal cheat sheet, never shared truth. Anything both sides must follow goes into a file in the repo that everyone can see.
- Words guide, the two narrow hooks block, tests and real tools prove — three different jobs, never confused (context is not enforcement, as Anthropic itself puts it).
- A noisy detector feeding a blocking gate teaches the agent to rubber-stamp — so detection stays precise (word-boundary level), and warnings never block anyone.

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
2. **Bootstrap scan** — `bootstrap-project-context.py` scans current files/config and writes **clues, not conclusions**: into `project-map.md`, `command-contract.md`, `bootstrap-report.md`, and `rule-candidates.md`, plus marked generated blocks in `drift-map.yml` and `adaptation-review.md` for the agent to tighten. A file named `sync.ts` is a *signal*, not proof of verified cloud sync.
3. **Adapt** *(agent-driven)* — following `.agent/workflows/adapt-rules.md`, the agent inspects current code, config, tests, and any old backups, writes **only verified facts** into `.agent/*`, tightens the drift-map globs to the project's real paths, and mirrors them into `.claude/rules/*`. Unprovable high-risk facts become `needs-user`.
4. **Validate** — `validate-installed-project.sh` checks that the structure exists, `CLAUDE.md` imports `@AGENTS.md`, the Codex skill tree matches the canonical one, scripts are executable, and (with the strict flags) that adaptation status, placeholders, and candidates are all handled. Form, not correctness.
5. **Grow** *(agent-driven)* — as code changes, the two scan scripts surface possibly stale docs and new candidates; the agent verifies, confirms unchanged, rejects, or marks `needs-user`.

</details>
