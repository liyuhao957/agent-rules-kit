# Claude Code + Codex Project Rules Kit

[English](./README.md) | [简体中文](./README.zh-CN.md)

This repository is a reusable template for projects that are worked on by both Claude Code and Codex.

The design goal is not to make a larger project encyclopedia. It is to make agents work from the same contract, verify current facts before acting, and close feature, logic, UI, data, and documentation loops.

## What This Kit Does

This kit gives Claude Code and Codex one shared project operating system:

- A short shared entrypoint: `AGENTS.md`.
- A Claude Code entrypoint that imports the same contract: `CLAUDE.md`.
- Shared project rules under `.agent/`.
- Codex and Claude Code skills/hooks that load the shared rules at the right time.
- Scripts that install, bootstrap, validate, detect drift, and generate rule-maintenance candidates.

The important idea is:

```text
agent starts in a project
  -> installs Rules
  -> scans current repo evidence
  -> adapts generic rules into verified project rules
  -> develops/reviews using those rules
  -> updates rules when durable project facts change
```

Rules should grow from verified evidence, not from old docs, memory, or filenames alone.

## Layout

```text
templates/project/
  AGENTS.md                 Shared entrypoint for Codex and other agents
  CLAUDE.md                 Claude Code entrypoint that imports AGENTS.md
  .agent/                   Shared project protocol and quality standards
  .agents/skills/           Codex skills that load shared .agent protocols
  .claude/skills/           Claude Code skills that load shared .agent protocols
  .claude/agents/           Claude Code subagent templates
  .claude/hooks/            Claude Code hook scripts (lifecycle reminders/guards)
  .codex/hooks/             Codex hook scripts (lifecycle reminders/guards)
  .codex/hooks.example.json Codex hook example
  .claude/settings.example.json Claude Code hook/settings example
```

## File Responsibilities

| Path | Purpose | Who uses it |
| --- | --- | --- |
| `AGENTS.md` | Shared, short project entrypoint and source-of-truth policy. | Codex, Claude Code through `CLAUDE.md`, other agents |
| `CLAUDE.md` | Thin Claude Code entrypoint that imports `@AGENTS.md`. | Claude Code |
| `.agent/index.md` | Routes agents to the right workflow/domain docs. | Both agents |
| `.agent/source-of-truth.md` | Defines what counts as proof and what must be rechecked. | Both agents |
| `.agent/adaptation-review.md` | Says whether installed rules are still generic or already adapted to this project. | Both agents |
| `.agent/product-invariants.md` | Durable product promises that future work should preserve. | Both agents |
| `.agent/user-journeys.md` | Main user flows and expected loop closure. | Both agents |
| `.agent/domains/*` | Focused rules for UI/copy, data/sync, build/test, release, localization, performance. | Both agents |
| `.agent/command-contract.md` | Verified commands plus generated command candidates. | Both agents |
| `.agent/drift-map.yml` | Maps changed code paths to docs that may need review. | Drift scripts and agents |
| `.agent/rule-candidates.md` | Automatic-growth inbox. Scripts add candidates; agents decide outcomes. | Both agents |
| `.agent/project-map.md` | Generated map from current repo files/config. It is a clue, not final truth. | Both agents |
| `.agent/bootstrap-report.md` | Generated bootstrap summary, old-rule clues, and adaptation TODOs. | Both agents |
| `.agents/skills/*` | Codex skill wrappers that load `.agent` workflows. | Codex |
| `.claude/skills/*`, `.claude/agents/*`, `.claude/hooks/*` | Claude Code-specific loaders and reminders. | Claude Code |
| `.codex/hooks.example.json` | Optional Codex hook configuration example. | Codex |
| `scripts/bootstrap-project-context.py` | Scans repo evidence and refreshes generated maps/candidates. | Agents |
| `scripts/check-doc-drift.py` | Reports which docs may need review after code changes. | Agents/hooks |
| `scripts/suggest-rule-updates.py` | Generates rule candidates from diffs, command candidates, old backups, and risk signals. | Agents/hooks |

## Recommended Agent-First Flow

First, clone this kit somewhere on your machine:

```bash
git clone https://github.com/liyuhao957/agent-rules-kit.git
```

In the commands below, `/path/to/agent-rules-kit` is wherever you cloned this kit, and `/path/to/project` is the target project you are installing into.

Do not treat a direct shell install as complete project setup. The ideal flow is:

1. Start Claude Code or Codex in the target project.
2. Ask the agent:

   > Install and adapt `/path/to/agent-rules-kit` for this project.
   > If this project already has `AGENTS.md` or `CLAUDE.md`, back them up first.
   > Old rules, Claude memory, Codex memory, handoffs, and summaries are clues only, not facts.
   > Promote only facts verified from current code, config, tests, docs, or tool output into `.agent/*`.
   > Put unverified or high-risk facts in `needs-user`; do not ask the user about ordinary candidates.
   > Mark `.agent/adaptation-review.md` as adapted and pass strict validation.

3. The agent runs:

```bash
/path/to/agent-rules-kit/scripts/agent-install-rules.sh --target /path/to/project
```

4. The agent follows `.agent/workflows/adapt-rules.md`, reads current code/config/docs, reviews old backups if present, and writes verified project facts into `.agent/*`.
5. The agent runs `python3 scripts/suggest-rule-updates.py` and handles every `.agent/rule-candidates.md` item by promoting, checking unchanged, rejecting, or marking `needs-user`.
6. The agent marks `.agent/adaptation-review.md` as `Status: adapted`.
7. The agent verifies:

```bash
/path/to/agent-rules-kit/scripts/validate-installed-project.sh /path/to/project --require-adapted --require-candidates-reviewed
```

For an existing project that already has agent rules:

```bash
/path/to/agent-rules-kit/scripts/agent-install-rules.sh --target /path/to/project --force
```

Old rule files are backed up under `.rules-kit/backups/rules-install-<timestamp>/` and must be read as clues during adaptation.

## Common Usage Patterns

### New Project

Start Claude Code or Codex in the new project and give the agent the recommended prompt above.

Expected result:

- Rules are installed.
- Bootstrap scans the current repository.
- The agent adapts `.agent/*` from actual code/config.
- Strict validation passes.
- Future agents can start from `AGENTS.md` instead of rediscovering the project from zero.

### Existing Project With Old Rules

Use `--force` through the agent-facing command.

Expected result:

- Old `AGENTS.md`, `CLAUDE.md`, `.agent`, `.agents`, `.claude`, and `.codex` paths are moved into `.rules-kit/backups/`.
- Old rules are reviewed as clues.
- Verified durable facts are promoted into the new `.agent/*`.
- Stale, contradictory, or unprovable old facts are rejected or written under `needs-user`.

This is the safe path when old Claude/Codex memory or old project docs may be wrong.

### Daily Feature Work

For normal implementation or review, the agent should:

1. Read `AGENTS.md`.
2. Open `.agent/index.md`.
3. Load only the relevant workflow/domain docs.
4. Inspect current code/config/tests before editing.
5. Run appropriate validation from `.agent/command-contract.md`.
6. Run drift/rule-candidate checks before finalizing non-trivial work.
7. Update `.agent/*` only when the change created or changed durable project knowledge.

Example: if a feature changes sync deletion behavior, the agent should inspect the real sync/data code, update the implementation, verify it, then decide whether `.agent/domains/data-sync.md` or `.agent/user-journeys.md` needs a rule update.

### Claude Code And Codex Handoff

The two agents do not need to share private memory to stay aligned.

They align through repository-visible files:

- `AGENTS.md` and `CLAUDE.md` for entry.
- `.agent/*` for durable project truth.
- `.agent/work/*` for optional handoff notes.
- `.agent/rule-candidates.md` for pending rule-maintenance decisions.

If Claude implements and Codex reviews, Codex should inspect the actual diff and evidence. If Codex implements and Claude continues, Claude should do the same. A handoff note is intent, not proof.

### Large Refactor Or Project Shape Change

Run bootstrap again after large structure changes:

```bash
python3 scripts/bootstrap-project-context.py
python3 scripts/check-doc-drift.py
python3 scripts/suggest-rule-updates.py
```

Then the agent should re-check `.agent/project-map.md`, `.agent/command-contract.md`, `.agent/drift-map.yml`, and `.agent/rule-candidates.md`.

### When Rules Become Noisy

Use `.agent/rule-health.md`.

Rules should be kept when they are durable and helpful. They should be rewritten, moved, or deleted when they are stale, duplicated, too specific, or causing noisy drift checks.

## What Actually Happens

### 1. Install

`agent-install-rules.sh` calls the lower-level installer with bootstrap enabled.

It writes the template files, records install metadata in `.agent/rules-kit.json`, backs up any existing rule files before replacing them (unless `--no-backup` is passed), and runs the bootstrap scanner.

After this phase, the project is only installed. It is not adapted yet. `.agent/adaptation-review.md` should still say `Status: pending`.

### 2. Bootstrap

`scripts/bootstrap-project-context.py` scans current repository files and config. It writes conservative, reviewable clues:

- `.agent/project-map.md`: detected project type, localization signals, path signals, command candidates.
- `.agent/command-contract.md`: generated command candidates, while preserving verified command inventory.
- `.agent/bootstrap-report.md`: what was detected, what old backups exist, and what the agent must review.
- `.agent/rule-candidates.md`: initial candidates for rule maintenance.

Bootstrap does not prove product intent. For example, a file named `sync.ts` is only a sync signal; it does not prove the product has verified cloud sync.

### 3. Adapt

Claude Code or Codex follows `.agent/workflows/adapt-rules.md`.

The agent inspects current code, config, tests, scripts, docs, generated files, old backups, and available tool output. Then it promotes only verified durable facts into `.agent/*`.

Typical adaptation output:

- `product-invariants.md`: what the product must keep true.
- `user-journeys.md`: the main user paths the agent should close when changing behavior.
- `domains/*.md`: domain-specific facts and verification rules.
- `command-contract.md`: commands the agent has actually verified or intentionally kept as candidates.
- `drift-map.yml`: project-specific path-to-doc ownership, trimmed so drift checks are useful instead of noisy.
- `tool-policy.md`: project tools, CLIs, MCPs, device/browser/database/remote dependencies.
- `adaptation-review.md`: final status, reviewed evidence, and high-risk unknowns.

Old `AGENTS.md`, `CLAUDE.md`, Claude memory, Codex memory, handoffs, and summaries are only clues. If a fact cannot be verified from current evidence, it is not promoted into official rules.

### 4. Validate

Strict validation checks that:

- The installed structure exists.
- `CLAUDE.md` imports `@AGENTS.md`.
- Required scripts are executable.
- `.agent/adaptation-review.md` says `Status: adapted`.
- `.agent/adaptation-review.md` has no remaining `pending` fields, such as `Adapted by:` or `Last reviewed:`.
- Adaptation checklist items are checked.
- `.agent/rule-candidates.md` has no ordinary `Status: pending` items.

Use:

```bash
/path/to/agent-rules-kit/scripts/validate-installed-project.sh /path/to/project --require-adapted --require-candidates-reviewed
```

### 5. Work

After adaptation, normal development uses the shared contract:

- Implementers read the relevant workflow/domain docs, then inspect real code before editing.
- Reviewers inspect current diff, code paths, and verification evidence instead of trusting handoffs.
- Continuers reconstruct state from git, files, and notes.
- Release work verifies live external state with real tools before claiming anything.

The agent should not load every rule file every time. It should start from `AGENTS.md` and `.agent/index.md`, then open only the workflow/domain docs needed for the task.

### 6. Grow

When code changes may affect durable project knowledge, the Rules kit grows through candidates:

```text
code/config/docs changed
  -> check-doc-drift.py reports possible affected docs
  -> suggest-rule-updates.py writes rule candidates
  -> agent inspects evidence
  -> agent promotes, checks unchanged, rejects, or marks needs-user
```

The script does not edit official rules by itself. The agent decides autonomously when evidence is enough. The user should only be pulled in for high-risk facts that cannot be proven and matter to the current task.

## What Is Automatic

Automatic:

- Back up old rule files during forced install.
- Install shared entrypoints, `.agent` protocols, skills, hooks examples, and helper scripts.
- Detect project shape from files/config.
- Generate command candidates.
- Generate review candidates from old rules in backups.
- Detect likely doc drift from changed paths.
- Generate rule-maintenance candidates.
- Validate whether adaptation and candidate review are complete.

Agent-driven:

- Decide which old-rule facts are true.
- Verify commands before putting them into the command contract.
- Trim noisy `drift-map.yml` entries.
- Promote useful candidates into `.agent/*`.
- Reject stale or overly specific rules.
- Mark high-risk unverified facts as `needs-user`.

Not automatic:

- Proving live App Store, production, billing, remote, device, credential, or user-data state without real tools.
- Blindly copying old `AGENTS.md` / `CLAUDE.md` into new rules.
- Turning every detected file or one-time incident into a durable rule.
- Guaranteeing Claude private memory and Codex private memory are correct or synchronized.

## What Gets Written

The installer writes the shared contract and helper scripts into the target project:

- `AGENTS.md`: shared entrypoint for Codex and other agents.
- `CLAUDE.md`: thin Claude Code entrypoint that imports `AGENTS.md`.
- `.agent/`: shared project rules, workflows, domains, adaptation status, command contract, drift map, and rule candidates.
- `.agents/skills/`: Codex skills that load the shared `.agent/` protocols.
- `.claude/skills/`, `.claude/agents/`, `.claude/hooks/`: Claude Code-specific helpers.
- `.codex/`: Codex hook examples.
- `scripts/check-doc-drift.py`, `scripts/suggest-rule-updates.py`, `scripts/bootstrap-project-context.py`.

Recommended version-control policy:

- Commit `AGENTS.md`, `CLAUDE.md`, `.agent/`, `.agents/`, `.codex/`, and `scripts/`.
- Decide per project whether to commit `.rules-kit/backups/`; it is useful migration evidence but may contain stale or bulky old rules.
- Decide per project whether `.claude/` should be committed. Some teams ignore it because Claude Code also has private local memory; the shared contract must still live in `.agent/`.
- Usually keep `.agent/work/*` local unless the team intentionally shares handoff notes.

## Low-Level Install Command

This lower-level command only installs templates and optional bootstrap candidates. It does not adapt rules to the project by itself.

```bash
/path/to/agent-rules-kit/scripts/install-rules.sh --target /path/to/project --bootstrap
```

If the project already has `AGENTS.md`, `CLAUDE.md`, `.agent`, `.agents`, `.claude`, or `.codex`, the installer refuses to overwrite by default. To replace them safely:

```bash
/path/to/agent-rules-kit/scripts/install-rules.sh --target /path/to/project --force
```

For existing projects, use both:

```bash
/path/to/agent-rules-kit/scripts/install-rules.sh --target /path/to/project --force --bootstrap
```

Existing rule files are backed up under:

```text
.rules-kit/backups/rules-install-<timestamp>/
```

After low-level install, an agent still needs to follow `.agent/workflows/adapt-rules.md` and review/customize:

- `AGENTS.md`
- `CLAUDE.md`
- `.agent/adaptation-review.md`
- `.agent/product-invariants.md`
- `.agent/user-journeys.md`
- `.agent/domains/*`
- `.agent/tool-policy.md`
- `.agent/command-contract.md` command inventory and generated candidates
- `.agent/drift-map.yml`
- `.agent/rule-candidates.md`
- `.agent/project-map.md`
- `.agent/bootstrap-report.md`

Validate an installed project:

```bash
/path/to/agent-rules-kit/scripts/validate-installed-project.sh /path/to/project
```

Validate that a project has been agent-adapted, not only installed:

```bash
/path/to/agent-rules-kit/scripts/validate-installed-project.sh /path/to/project --require-adapted --require-candidates-reviewed
```

If you installed without `--bootstrap`, run:

```bash
/path/to/agent-rules-kit/scripts/bootstrap-project.sh /path/to/project
```

Add this to the target project's `.gitignore` if you want handoff notes to stay local:

```gitignore
.agent/work/*
!.agent/work/README.md
```

## Philosophy

- Private Claude memory and private Codex memory are hints, not shared project truth.
- Old `AGENTS.md`, `CLAUDE.md`, handoffs, summaries, and memories are clues only. Current evidence wins.
- Shared project rules live in the repository.
- Docs route the agent to the right checks; current code, config, tests, builds, tools, and live remote state prove facts.
- Skills improve automatic workflow loading, but high-risk work still needs explicit verification and tool output.
- Hooks can catch repeated mistakes, but they do not replace agent judgment.
- Drift checks discover likely doc-review needs from changed paths. Agents decide autonomously whether to promote, reject, or leave a high-risk fact as `needs-user`.
- Command contracts keep verified validation commands in one place; bootstrap only refreshes clearly marked candidates.
- Rule health checks keep the rules kit from growing into a noisy encyclopedia.

## Drift Checks

After installing into a project, run this before finalizing non-trivial changes:

```bash
python3 scripts/check-doc-drift.py
python3 scripts/suggest-rule-updates.py
```

`check-doc-drift.py` maps changed files to `.agent` docs through `.agent/drift-map.yml`. It does not auto-edit docs.

`suggest-rule-updates.py` writes `.agent/rule-candidates.md`. The agent should resolve candidates autonomously:

- `promoted`
- `checked-unchanged`
- `rejected`
- `needs-user`

Only mark `needs-user` when the fact is high-risk and cannot be verified from repo/tool evidence. Do not leave ordinary completed work with `Status: pending` candidates.

Customize `.agent/drift-map.yml` for each real project after installation. The default map is intentionally broad enough to be useful, but not a substitute for project-specific path ownership.

## Optional Hook Enablement

Hook files are installed as examples so projects can opt in deliberately.

To enable Codex hooks, review and copy:

```bash
cp .codex/hooks.example.json .codex/hooks.json
```

To enable Claude Code hooks, review and copy:

```bash
cp .claude/settings.example.json .claude/settings.json
```

Do this only after reviewing the hook commands for the project. Hooks are reminders and guards, not a replacement for validation.

## What This Kit Borrows From Agent Tooling

- Short entrypoints: `AGENTS.md` and `CLAUDE.md` stay small.
- Progressive disclosure: Claude and Codex skills load task workflows only when relevant.
- Shared protocol: both agents read `.agent/` instead of maintaining separate long rule sets.
- Tool evidence: MCP, CLI, browser, device, database, and remote tools are treated as proof sources.
- Hooks: lifecycle reminders surface quality gates and drift checks at the moment agents tend to forget them.
- Memory boundary: private memories stay personal; shared durable facts live in the repo.
- Command inventory: validation commands live in `.agent/command-contract.md` and must be verified before use.
- Rule maintenance: `.agent/rule-health.md` describes when to prune, move, rewrite, or delete rules.
