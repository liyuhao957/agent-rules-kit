#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<EOF
Usage: agent-install-rules.sh --target <project-root> [--force] [--no-backup]

Agent-facing entrypoint:
  1. Installs Rules into the target project.
  2. Runs bootstrap scanning.
  3. Leaves .agent/adaptation-review.md in pending state.
  4. Prints the required agent adaptation workflow.

This command does not complete project adaptation by itself. A Claude/Codex
agent must inspect current code/config and update .agent/* before strict
validation can pass.
EOF
}

args=()
target=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      target="${2:-}"
      args+=("$1" "$2")
      shift 2
      ;;
    --force|--no-backup)
      args+=("$1")
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$target" ]]; then
  echo "Missing --target <project-root>" >&2
  usage >&2
  exit 2
fi

bash "$script_dir/install-rules.sh" "${args[@]}" --bootstrap

cat <<EOF

Agent adaptation required:
  cd "$target"
  1. Read AGENTS.md and .agent/workflows/adapt-rules.md.
  2. Inspect current code/config/tests/scripts/docs and old backups if present.
  3. Promote verified facts into .agent/product-invariants.md, .agent/user-journeys.md, .agent/command-contract.md, relevant .agent/domains/*, and .agent/drift-map.yml.
  4. Run python3 scripts/suggest-rule-updates.py and resolve every .agent/rule-candidates.md item without asking the user for ordinary candidates.
  5. Fill .agent/adaptation-review.md and change Status: pending to Status: adapted.
  6. Run:
     bash "$script_dir/validate-installed-project.sh" "$target" --require-adapted --require-candidates-reviewed
     python3 scripts/check-doc-drift.py
EOF
