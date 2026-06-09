#!/usr/bin/env bash
set -euo pipefail

target="${1:-}"

if [[ -z "$target" ]]; then
  echo "Usage: bootstrap-project.sh <project-root>" >&2
  exit 2
fi

target="$(cd "$target" && pwd)"

if [[ ! -x "$target/scripts/bootstrap-project-context.py" ]]; then
  echo "FAIL: $target/scripts/bootstrap-project-context.py not found or not executable. Install Rules first." >&2
  exit 1
fi

(cd "$target" && python3 scripts/bootstrap-project-context.py)

