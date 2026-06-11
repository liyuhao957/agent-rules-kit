#!/usr/bin/env bash
# Lifecycle integration tests: install / reinstall / uninstall on throwaway
# projects under a temp dir. Asserts the kit fully removes itself and that a
# --force reinstall does not corrupt the "restore my original files" contract.
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
install="$repo_root/scripts/install-rules.sh"
uninstall="$repo_root/scripts/uninstall-rules.sh"

pass=0
fail=0
fails=()
check() { # name, condition-already-evaluated ($?=0 ok), detail
  if [[ "$1" -eq 0 ]]; then pass=$((pass+1)); else fail=$((fail+1)); fails+=("$2"); fi
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# --- Scenario A: greenfield install -> --force reinstall -> uninstall ---
# The kit must be GONE after uninstall (the round-1 self-undo bug restored it).
projA="$work/greenfield"
mkdir -p "$projA/src"
( cd "$projA" && git init -q && git config user.email t@t && git config user.name t \
  && printf 'console.log(1)\n' > src/app.js && printf '{"name":"a"}\n' > package.json \
  && git add -A && git commit -qm init )

bash "$install" --target "$projA" >/dev/null 2>&1
bash "$install" --target "$projA" --force >/dev/null 2>&1
bash "$uninstall" --target "$projA" >/dev/null 2>&1

[[ ! -e "$projA/AGENTS.md" ]]; check $? "A: AGENTS.md should be gone after uninstall"
[[ ! -e "$projA/.agent" ]]; check $? "A: .agent/ should be gone after uninstall"
[[ ! -e "$projA/.claude" ]]; check $? "A: .claude/ should be gone after uninstall"
[[ ! -e "$projA/.codex" ]]; check $? "A: .codex/ should be gone after uninstall"
[[ ! -e "$projA/.agents" ]]; check $? "A: .agents/ should be gone after uninstall"
[[ -f "$projA/src/app.js" ]]; check $? "A: user source must survive"
[[ -f "$projA/package.json" ]]; check $? "A: user package.json must survive"

# --- Scenario B: pre-existing CLAUDE.md -> --force install -> --force reinstall -> uninstall ---
# The user's original CLAUDE.md content must be restored verbatim.
projB="$work/preexisting"
mkdir -p "$projB"
( cd "$projB" && git init -q && git config user.email t@t && git config user.name t )
printf 'MY-ORIGINAL-CLAUDE-LINE\n' > "$projB/CLAUDE.md"
( cd "$projB" && git add -A && git commit -qm init )

bash "$install" --target "$projB" --force >/dev/null 2>&1
bash "$install" --target "$projB" --force >/dev/null 2>&1
bash "$uninstall" --target "$projB" >/dev/null 2>&1

if [[ -f "$projB/CLAUDE.md" ]] && grep -q 'MY-ORIGINAL-CLAUDE-LINE' "$projB/CLAUDE.md" \
   && ! grep -q 'Claude Code Notes' "$projB/CLAUDE.md"; then
  check 0 ""
else
  check 1 "B: original CLAUDE.md must be restored verbatim (got: $(cat "$projB/CLAUDE.md" 2>/dev/null | head -1))"
fi

# --- Scenario C: --force --no-backup must REPLACE, not merge (no stale kit files) ---
projC="$work/forcereset"
mkdir -p "$projC"
( cd "$projC" && git init -q && git config user.email t@t && git config user.name t )
bash "$install" --target "$projC" >/dev/null 2>&1
# Plant a stale kit-shaped file that a newer kit version would have removed.
mkdir -p "$projC/.claude/skills/obsolete-old-skill"
printf 'stale\n' > "$projC/.claude/skills/obsolete-old-skill/SKILL.md"
printf 'stale\n' > "$projC/.agent/domains/obsolete-domain.md"
bash "$install" --target "$projC" --force --no-backup >/dev/null 2>&1
[[ ! -e "$projC/.claude/skills/obsolete-old-skill" ]]; check $? "C: --force --no-backup must drop stale skill"
[[ ! -e "$projC/.agent/domains/obsolete-domain.md" ]]; check $? "C: --force --no-backup must drop stale domain doc"

total=$((pass+fail))
if [[ "$fail" -eq 0 ]]; then
  echo "[OK] lifecycle: $pass/$total passed"
  exit 0
else
  echo "[FAIL] lifecycle: $pass/$total passed"
  for f in "${fails[@]}"; do echo "    - $f"; done
  exit 1
fi
