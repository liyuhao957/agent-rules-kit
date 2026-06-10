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

# Glob mirror parity: .agent/drift-map.yml globs are hand-mirrored into
# .claude/rules/*.md frontmatter. Divergence is a warning by default and a
# failure under --require-adapted.
glob_parity_ok=1
if ! python3 - "$target" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
drift_path = root / ".agent/drift-map.yml"
rules_dir = root / ".claude/rules"


def parse_drift_map(path: Path) -> list[dict[str, object]]:
    # Same minimal parser as scripts/check-doc-drift.py.
    rules: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    active = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if re.match(r"^\s*-\s+name:\s*", line):
            if current:
                rules.append(current)
            current = {"name": line.split("name:", 1)[1].strip().strip('"'), "paths": []}
            active = None
            continue
        if current is None:
            continue
        stripped = line.strip()
        if stripped in {"paths:", "docs:"}:
            active = stripped[:-1]
            continue
        if stripped.startswith("reason:"):
            active = None
            continue
        if stripped.startswith("- ") and active == "paths":
            current["paths"].append(stripped[2:].strip().strip('"'))  # type: ignore[union-attr]
    if current:
        rules.append(current)
    return rules


def frontmatter_globs(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return []
    globs: list[str] = []
    in_paths = False
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped == "paths:":
            in_paths = True
            continue
        if stripped.endswith(":") and not stripped.startswith("- "):
            in_paths = False
            continue
        if in_paths and stripped.startswith("- "):
            globs.append(stripped[2:].strip().strip('"').strip("'"))
    return globs


rules = parse_drift_map(drift_path) if drift_path.is_file() else []
drift_globs = {glob for rule in rules for glob in rule["paths"]}  # type: ignore[union-attr]
pointer_files = sorted(rules_dir.glob("*.md")) if rules_dir.is_dir() else []
problems: list[str] = []

for pointer in pointer_files:
    for glob in frontmatter_globs(pointer):
        if glob not in drift_globs:
            problems.append(f".claude/rules/{pointer.name}: glob `{glob}` is not in .agent/drift-map.yml")

for rule in rules:
    pointer = rules_dir / f"{rule['name']}.md"
    if not pointer.is_file():
        continue
    pointer_globs = set(frontmatter_globs(pointer))
    for glob in rule["paths"]:  # type: ignore[union-attr]
        if glob not in pointer_globs:
            problems.append(f"drift-map rule `{rule['name']}`: glob `{glob}` missing from .claude/rules/{pointer.name}")

if problems:
    print("WARN: .agent/drift-map.yml and .claude/rules/*.md frontmatter globs have diverged; mirror them (see .claude/rules/rules-kit.md):")
    for problem in problems:
        print(f"  - {problem}")
    sys.exit(1)
sys.exit(0)
PY
then
  glob_parity_ok=0
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
  if grep -Eq -- '^- pending[[:space:]]*$' "$review"; then
    echo "FAIL: .agent/adaptation-review.md still contains '- pending' placeholder entries. Replace each with real findings:" >&2
    grep -En -- '^- pending[[:space:]]*$' "$review" | sed 's/^/  line /' >&2
    exit 1
  fi
  marker_files=()
  for doc in command-contract.md user-journeys.md product-invariants.md; do
    if [[ -f "$target/.agent/$doc" ]] && grep -Fq -e "project-specific" -e "Replace this template" "$target/.agent/$doc"; then
      marker_files+=(".agent/$doc")
    fi
  done
  if [[ ${#marker_files[@]} -gt 0 ]]; then
    echo "FAIL: literal template markers ('project-specific' / 'Replace this template') remain in:" >&2
    printf '  - %s\n' "${marker_files[@]}" >&2
    echo "Rewrite them with verified project facts, or as 'needs-user: ...' entries when unverifiable." >&2
    exit 1
  fi
  if [[ "$glob_parity_ok" -ne 1 ]]; then
    echo "FAIL: .agent/drift-map.yml and .claude/rules/*.md frontmatter globs have diverged (see WARN above). Mirror the globs before marking the project adapted." >&2
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
