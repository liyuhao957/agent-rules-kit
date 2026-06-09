#!/usr/bin/env bash
set -euo pipefail

root="${1:-templates/project}"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

need_file() {
  [ -f "$root/$1" ] || fail "missing $1"
}

need_dir() {
  [ -d "$root/$1" ] || fail "missing $1"
}

need_contains() {
  local file="$1"
  local text="$2"
  grep -Fq -- "$text" "$root/$file" || fail "$file does not contain: $text"
}

need_file "AGENTS.md"
need_file "CLAUDE.md"
need_contains "CLAUDE.md" "@AGENTS.md"

for file in \
  ".agent/index.md" \
  ".agent/source-of-truth.md" \
  ".agent/quality-gates.md" \
  ".agent/memory-policy.md" \
  ".agent/skill-policy.md" \
  ".agent/tool-policy.md" \
  ".agent/command-contract.md" \
  ".agent/adaptation-review.md" \
  ".agent/verification-map.md" \
  ".agent/doc-drift.md" \
  ".agent/drift-map.yml" \
  ".agent/rule-candidates.md" \
  ".agent/rule-health.md" \
  ".agent/external-practices.md" \
  ".agent/project-map.md" \
  ".agent/bootstrap-report.md" \
  ".agent/handoff-template.md"; do
  need_file "$file"
done

for workflow in adapt-rules implement review continue release; do
  need_file ".agent/workflows/$workflow.md"
done

for domain in ui-copy build-test data-sync localization performance release; do
  need_file ".agent/domains/$domain.md"
done

for skill in adapt-rules implement review continue quality-gate doc-drift drift-check rule-health release-safety; do
  need_file ".agents/skills/$skill/SKILL.md"
  need_file ".claude/skills/$skill/SKILL.md"
done

need_dir ".claude/agents"
need_file ".codex/hooks.example.json"
need_file ".claude/settings.example.json"
need_file "scripts/bootstrap-project-context.py"
need_file ".codex/hooks/stop_quality_reminder.py"
need_file ".codex/hooks/pre_bash_release_guard.py"
need_file ".claude/hooks/stop_quality_reminder.py"
need_file ".claude/hooks/pre_bash_release_guard.py"
need_file "scripts/check-doc-drift.py"
need_file "scripts/suggest-rule-updates.py"

need_contains "AGENTS.md" "Private Claude memory and private Codex memory are not shared project truth"
need_contains "AGENTS.md" ".agent/adaptation-review.md"
need_contains "AGENTS.md" "python3 scripts/suggest-rule-updates.py"
need_contains "AGENTS.md" "python3 scripts/check-doc-drift.py"
need_contains "AGENTS.md" "python3 scripts/bootstrap-project-context.py"
need_contains ".agent/adaptation-review.md" "Status:"
need_contains ".agent/adaptation-review.md" "BEGIN GENERATED ADAPTATION EVIDENCE"
need_contains ".agent/workflows/adapt-rules.md" "--require-adapted"
need_contains ".agent/workflows/adapt-rules.md" "--require-candidates-reviewed"
need_contains ".agent/quality-gates.md" "Intent Loop"
need_contains ".agent/quality-gates.md" "Drift Loop"
need_contains ".agent/quality-gates.md" "python3 scripts/check-doc-drift.py"
need_contains ".agent/tool-policy.md" "Do Not Infer Live State"
need_contains ".agent/skill-policy.md" "Skills are workflow loaders"
need_contains ".agent/skill-policy.md" "python3 scripts/check-doc-drift.py"
need_contains ".agent/command-contract.md" "Command Inventory"
need_contains ".agent/command-contract.md" "BEGIN GENERATED COMMAND CANDIDATES"
need_contains ".agent/rule-health.md" "Rules can rot"
need_contains ".agent/external-practices.md" "Adopted"
need_contains ".agent/project-map.md" "Project Map"
need_contains ".agent/bootstrap-report.md" "Bootstrap Report"
need_contains ".agent/doc-drift.md" "Update shared docs when"
need_contains ".agent/doc-drift.md" ".agent/drift-map.yml"
need_contains ".agent/rule-candidates.md" "BEGIN GENERATED RULE CANDIDATES"
need_contains ".agent/rule-candidates.md" "Agent rule: decide autonomously"
need_contains ".agent/drift-map.yml" "rules:"
need_contains ".agent/drift-map.yml" "command-contract"
need_contains "scripts/check-doc-drift.py" "Doc drift check:"
need_contains "scripts/suggest-rule-updates.py" "Rule candidates:"
need_contains "scripts/bootstrap-project-context.py" "Bootstrap complete:"
need_contains "scripts/bootstrap-project-context.py" "GENERATED PROJECT DRIFT CANDIDATES"
need_contains "scripts/bootstrap-project-context.py" "GENERATED ADAPTATION EVIDENCE"

printf 'OK: rules template is structurally complete at %s\n' "$root"
