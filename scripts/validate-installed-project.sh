#!/usr/bin/env bash
set -euo pipefail

target=""
require_adapted=0
require_candidates_reviewed=0

usage() {
  echo "Usage: validate-installed-project.sh <project-root> [--require-adapted] [--require-candidates-reviewed]" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --require-adapted)
      require_adapted=1
      shift
      ;;
    --require-candidates-reviewed)
      require_candidates_reviewed=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$target" ]]; then
        target="$1"
        shift
      else
        echo "Unknown argument: $1" >&2
        usage
        exit 2
      fi
      ;;
  esac
done

if [[ -z "$target" ]]; then
  usage
  exit 2
fi

target="$(cd "$target" && pwd)"
rules_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash "$rules_root/scripts/validate-rules-template.sh" "$target"

if [[ ! -f "$target/.agent/rules-kit.json" ]]; then
  echo "FAIL: missing .agent/rules-kit.json" >&2
  exit 1
fi

if ! grep -Fq "@AGENTS.md" "$target/CLAUDE.md"; then
  echo "FAIL: CLAUDE.md does not import @AGENTS.md" >&2
  exit 1
fi

if [[ ! -f "$target/.codex/hooks.json" ]]; then
  echo "FAIL: missing .codex/hooks.json. Rules installs active Codex hooks by default." >&2
  exit 1
fi

if [[ ! -f "$target/.claude/settings.json" ]]; then
  echo "FAIL: missing .claude/settings.json. Rules installs active Claude Code hooks by default." >&2
  exit 1
fi

if [[ ! -d "$target/.agents/skills" ]]; then
  echo "FAIL: missing .agents/skills. The installer generates the Codex skill tree from .claude/skills." >&2
  exit 1
fi

if [[ -x "$target/scripts/check-doc-drift.py" ]]; then
  (cd "$target" && python3 scripts/check-doc-drift.py >/dev/null)
else
  echo "FAIL: scripts/check-doc-drift.py is not executable" >&2
  exit 1
fi

if [[ ! -x "$target/scripts/bootstrap-project-context.py" ]]; then
  echo "FAIL: scripts/bootstrap-project-context.py is not executable" >&2
  exit 1
fi

if [[ ! -x "$target/scripts/suggest-rule-updates.py" ]]; then
  echo "FAIL: scripts/suggest-rule-updates.py is not executable" >&2
  exit 1
fi

if [[ "$require_adapted" -eq 1 ]]; then
  review="$target/.agent/adaptation-review.md"
  if [[ ! -f "$review" ]]; then
    echo "FAIL: missing .agent/adaptation-review.md" >&2
    exit 1
  fi
  if ! grep -Eq '^Status:[[:space:]]*adapted[[:space:]]*$' "$review"; then
    echo "FAIL: Rules are installed but not adapted. .agent/adaptation-review.md must say 'Status: adapted'." >&2
    exit 1
  fi
  if grep -Eq '^Adapted by:[[:space:]]*pending[[:space:]]*$' "$review"; then
    echo "FAIL: .agent/adaptation-review.md still has 'Adapted by: pending'" >&2
    exit 1
  fi
  if grep -Eq '^Last reviewed:[[:space:]]*pending[[:space:]]*$' "$review"; then
    echo "FAIL: .agent/adaptation-review.md still has 'Last reviewed: pending'" >&2
    exit 1
  fi
  if grep -Fq -- "- [ ]" "$review"; then
    echo "FAIL: .agent/adaptation-review.md has unchecked adaptation checklist items" >&2
    exit 1
  fi
fi

if [[ "$require_candidates_reviewed" -eq 1 ]]; then
  candidates="$target/.agent/rule-candidates.md"
  if [[ ! -f "$candidates" ]]; then
    echo "FAIL: missing .agent/rule-candidates.md" >&2
    exit 1
  fi
  (cd "$target" && python3 scripts/suggest-rule-updates.py --quiet)
  if grep -Eq '^Status:[[:space:]]*pending[[:space:]]*$' "$candidates"; then
    echo "FAIL: .agent/rule-candidates.md has pending candidates. Agent must promote, check unchanged, reject, or mark needs-user." >&2
    exit 1
  fi
  if python3 - "$candidates" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
bad = False
for section in re.split(r"(?=^### )", text, flags=re.MULTILINE):
    if not section.startswith("### "):
        continue
    status = re.search(r"^Status:\s*([A-Za-z-]+)\s*$", section, flags=re.MULTILINE)
    notes = re.search(r"Decision notes:\n(?P<notes>.*?)(?:\n\n|\Z)", section, flags=re.DOTALL)
    if status and status.group(1) != "pending" and notes:
        note_lines = [line.strip() for line in notes.group("notes").splitlines() if line.strip()]
        if note_lines == ["- pending"]:
            bad = True
            break
sys.exit(0 if bad else 1)
PY
  then
    echo "FAIL: .agent/rule-candidates.md has handled candidates with pending decision notes" >&2
    exit 1
  fi
fi

echo "OK: Rules kit installation is valid at $target"
