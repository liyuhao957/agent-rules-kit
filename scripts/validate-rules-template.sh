#!/usr/bin/env bash
set -euo pipefail

# --installed relaxes the fixed domain/pointer lists: an adapted project may
# prune domains it does not use (a CLI has no ui-copy/localization), so we
# validate whatever domains and pointers exist for consistency instead of
# requiring the full consumer-app set. The kit's own template (no flag) stays
# strict so it always ships every domain.
root=""
installed=0
for arg in "$@"; do
  case "$arg" in
    --installed) installed=1 ;;
    *) root="$arg" ;;
  esac
done
root="${root:-templates/project}"

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

if [ "$installed" -eq 1 ]; then
  # Adapted project: at least one domain doc must remain, but the project may
  # have pruned domains it does not use.
  if ! ls "$root"/.agent/domains/*.md >/dev/null 2>&1; then
    fail ".agent/domains/ has no domain docs"
  fi
else
  for domain in ui-copy build-test data-sync localization performance release; do
    need_file ".agent/domains/$domain.md"
  done
fi

# .claude/skills is the canonical skill tree. .agents/skills (Codex) is
# generated at install time; when present (installed projects) it must be
# identical so the two tools never diverge.
for skill in adapt-rules implement review-changes continue quality-gate doc-drift rule-health release-safety; do
  need_file ".claude/skills/$skill/SKILL.md"
done

if [ -d "$root/.agents/skills" ]; then
  diff -r "$root/.claude/skills" "$root/.agents/skills" >/dev/null 2>&1 \
    || fail ".agents/skills differs from canonical .claude/skills (regenerate it at install)"
fi

# Path-scoped pointer rules: Claude's on-demand loading of domain docs.
need_file ".claude/rules/rules-kit.md"
need_contains ".claude/rules/rules-kit.md" "paths:"
if [ "$installed" -eq 1 ]; then
  # Validate whatever pointers exist: each must declare paths:, and any domain
  # doc it references must still exist (so a pruned domain leaves no dangling
  # pointer). A pointer may reference non-domain docs (e.g. docs.md), so the
  # check is by reference, not by name.
  for pointer in "$root"/.claude/rules/*.md; do
    name="$(basename "$pointer" .md)"
    [ "$name" = "rules-kit" ] && continue
    need_contains ".claude/rules/$name.md" "paths:"
    while IFS= read -r ref; do
      [ -n "$ref" ] || continue
      [ -f "$root/$ref" ] || fail ".claude/rules/$name.md references missing $ref (prune the pointer and its doc together)"
    done < <(grep -oE '\.agent/domains/[A-Za-z0-9_-]+\.md' "$pointer" | sort -u)
  done
else
  for rule in ui-copy data-sync build-test localization release performance; do
    need_file ".claude/rules/$rule.md"
    need_contains ".claude/rules/$rule.md" "paths:"
    need_contains ".claude/rules/$rule.md" ".agent/domains/"
  done
fi

need_dir ".claude/agents"
need_file ".codex/hooks.example.json"
need_file ".claude/settings.example.json"
need_file "scripts/bootstrap-project-context.py"
need_file ".codex/hooks/stop_quality_reminder.py"
need_file ".codex/hooks/pre_bash_release_guard.py"
need_file ".codex/hooks/post_edit_domain_router.py"
need_file ".claude/hooks/stop_quality_reminder.py"
need_file ".claude/hooks/pre_bash_release_guard.py"
need_file "scripts/check-doc-drift.py"
need_file "scripts/suggest-rule-updates.py"

# The two stop hooks must stay identical (same contract on both tools).
diff "$root/.claude/hooks/stop_quality_reminder.py" "$root/.codex/hooks/stop_quality_reminder.py" >/dev/null 2>&1 \
  || fail ".claude and .codex stop_quality_reminder.py copies differ"
diff "$root/.claude/hooks/pre_bash_release_guard.py" "$root/.codex/hooks/pre_bash_release_guard.py" >/dev/null 2>&1 \
  || fail ".claude and .codex pre_bash_release_guard.py copies differ"

need_contains "AGENTS.md" "Private Claude memory and private Codex memory are not shared project truth"
need_contains "AGENTS.md" ".agent/adaptation-review.md"
need_contains "AGENTS.md" "python3 scripts/suggest-rule-updates.py"
need_contains "AGENTS.md" "python3 scripts/check-doc-drift.py"
need_contains "AGENTS.md" "python3 scripts/bootstrap-project-context.py"
need_contains "AGENTS.md" "Durable rules stay in repository-visible"
need_contains "AGENTS.md" "On-Demand Context Routing"
need_contains "CLAUDE.md" ".claude/rules/"
need_contains ".agent/adaptation-review.md" "Status:"
need_contains ".agent/adaptation-review.md" "BEGIN GENERATED ADAPTATION EVIDENCE"
need_contains ".agent/workflows/adapt-rules.md" "--require-adapted"
need_contains ".agent/workflows/adapt-rules.md" "--require-candidates-reviewed"
need_contains ".agent/workflows/adapt-rules.md" "mirror them into"
need_contains ".agent/index.md" "Task Lifecycle"
need_contains ".agent/quality-gates.md" "Intent Loop"
need_contains ".agent/quality-gates.md" "Drift Loop"
need_contains ".agent/quality-gates.md" "python3 scripts/check-doc-drift.py"
need_contains ".agent/tool-policy.md" "Do Not Infer Live State"
need_contains ".agent/tool-policy.md" "block only narrow high-risk"
need_contains ".agent/skill-policy.md" "Skills are workflow loaders"
need_contains ".agent/skill-policy.md" "Skills are adapters, not the rule source"
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
need_contains "scripts/suggest-rule-updates.py" "segmentize"
need_contains "scripts/bootstrap-project-context.py" "Bootstrap complete:"
need_contains "scripts/bootstrap-project-context.py" "GENERATED PROJECT DRIFT CANDIDATES"
need_contains "scripts/bootstrap-project-context.py" "GENERATED ADAPTATION EVIDENCE"
need_contains ".codex/hooks/pre_bash_release_guard.py" "RULES_HOOK_ALLOW_RISK"
need_contains ".codex/hooks/pre_bash_release_guard.py" "Rules hook blocked a high-risk shell command"
need_contains ".claude/hooks/pre_bash_release_guard.py" "RULES_HOOK_ALLOW_RISK"
need_contains ".claude/hooks/pre_bash_release_guard.py" "Rules hook blocked a high-risk shell command"
need_contains ".codex/hooks/stop_quality_reminder.py" "RULES_HOOK_ALLOW_PENDING"
need_contains ".codex/hooks/stop_quality_reminder.py" "Rules hook blocked finalization"
need_contains ".codex/hooks/stop_quality_reminder.py" "stop_hook_active"
need_contains ".claude/hooks/stop_quality_reminder.py" "RULES_HOOK_ALLOW_PENDING"
need_contains ".claude/hooks/stop_quality_reminder.py" "Rules hook blocked finalization"
need_contains ".claude/hooks/stop_quality_reminder.py" "stop_hook_active"
need_contains ".codex/hooks/post_edit_domain_router.py" "additionalContext"
need_contains ".codex/hooks.example.json" "post_edit_domain_router.py"

printf 'OK: rules template is structurally complete at %s\n' "$root"
