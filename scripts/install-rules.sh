#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rules_root="$(cd "$script_dir/.." && pwd)"
template_dir="$rules_root/templates/project"
version="$(tr -d '[:space:]' < "$rules_root/VERSION")"

target=""
force=0
backup=1
dry_run=0
bootstrap=0

usage() {
  cat <<EOF
Usage: install-rules.sh --target <project-root> [options]

Options:
  --target <path>   Project root to install into.
  --force           Replace existing rule files after backing them up.
  --no-backup       Do not back up existing files. Requires --force.
  --dry-run         Print planned actions without writing.
  --bootstrap       Scan project files after install and generate review candidates for agent adaptation.
  -h, --help        Show this help.

Default behavior:
  - Refuses to overwrite existing rule files unless --force is provided.
  - Backs up existing rule files to .rules-kit/backups/rules-install-<timestamp>/.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      target="${2:-}"
      shift 2
      ;;
    --force)
      force=1
      shift
      ;;
    --no-backup)
      backup=0
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --bootstrap)
      bootstrap=1
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

if [[ "$backup" -eq 0 && "$force" -ne 1 ]]; then
  echo "--no-backup requires --force" >&2
  exit 2
fi

target="$(cd "$target" && pwd)"

if [[ ! -d "$template_dir" ]]; then
  echo "Template directory not found: $template_dir" >&2
  exit 1
fi

managed_paths=(
  "AGENTS.md"
  "CLAUDE.md"
  ".agent"
  ".agents"
  ".claude"
  ".codex"
  "scripts/check-doc-drift.py"
  "scripts/bootstrap-project-context.py"
  "scripts/suggest-rule-updates.py"
)

existing=()
for path in "${managed_paths[@]}"; do
  if [[ -e "$target/$path" ]]; then
    existing+=("$path")
  fi
done

if [[ ${#existing[@]} -gt 0 && "$force" -ne 1 ]]; then
  echo "Existing rule paths found in $target:" >&2
  printf '  - %s\n' "${existing[@]}" >&2
  echo "Re-run with --force to back them up and replace them." >&2
  exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="$target/.rules-kit/backups/rules-install-$timestamp"

run() {
  if [[ "$dry_run" -eq 1 ]]; then
    printf '[dry-run] %q' "$1"
    shift
    for arg in "$@"; do
      printf ' %q' "$arg"
    done
    printf '\n'
  else
    "$@"
  fi
}

echo "Installing Rules kit $version into $target"

if [[ ${#existing[@]} -gt 0 && "$backup" -eq 1 ]]; then
  echo "Backing up existing rule paths to $backup_dir"
  if [[ "$dry_run" -ne 1 ]]; then
    mkdir -p "$backup_dir"
  fi
  for path in "${existing[@]}"; do
    parent="$(dirname "$backup_dir/$path")"
    if [[ "$dry_run" -eq 1 ]]; then
      echo "[dry-run] mkdir -p $parent"
      echo "[dry-run] mv $target/$path $backup_dir/$path"
    else
      mkdir -p "$parent"
      mv "$target/$path" "$backup_dir/$path"
    fi
  done
fi

if [[ "$dry_run" -eq 1 ]]; then
  echo "[dry-run] copy template files from $template_dir to $target"
  echo "[dry-run] write active hook configs from .codex/hooks.example.json and .claude/settings.example.json"
  echo "[dry-run] generate .agents/skills (Codex) from canonical .claude/skills"
else
  mkdir -p "$target"
  cp -R "$template_dir"/. "$target"/
  cp "$target/.codex/hooks.example.json" "$target/.codex/hooks.json"
  cp "$target/.claude/settings.example.json" "$target/.claude/settings.json"
  # .claude/skills is the canonical tree; the Codex tree is generated, never
  # hand-maintained, so the two cannot drift apart.
  rm -rf "$target/.agents"
  mkdir -p "$target/.agents"
  cp -R "$target/.claude/skills" "$target/.agents/skills"
  find "$target" -path '*/__pycache__*' -prune -exec rm -rf {} + 2>/dev/null || true
  chmod +x "$target/scripts/check-doc-drift.py" \
    "$target/scripts/bootstrap-project-context.py" \
    "$target/scripts/suggest-rule-updates.py" \
    "$target/.codex/hooks/"*.py \
    "$target/.claude/hooks/"*.py 2>/dev/null || true
fi

metadata="$target/.agent/rules-kit.json"
if [[ "$dry_run" -eq 1 ]]; then
  echo "[dry-run] write $metadata"
else
  cat > "$metadata" <<EOF
{
  "rulesKitVersion": "$version",
  "installedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source": "$rules_root",
  "template": "templates/project",
  "backup": $(if [[ ${#existing[@]} -gt 0 && "$backup" -eq 1 ]]; then printf '"%s"' "$backup_dir"; else printf 'null'; fi)
}
EOF
fi

if [[ "$dry_run" -ne 1 ]]; then
  if [[ "$bootstrap" -eq 1 ]]; then
    (cd "$target" && python3 scripts/bootstrap-project-context.py)
  fi
  bash "$rules_root/scripts/validate-installed-project.sh" "$target"
fi

if [[ "$bootstrap" -eq 1 ]]; then
  echo "Rules kit installed and bootstrapped."
  echo "Status: pending agent adaptation. A Claude/Codex agent must run .agent/workflows/adapt-rules.md and mark .agent/adaptation-review.md as adapted before these are treated as project rules."
else
  echo "Rules kit installed."
  echo "Status: pending agent adaptation. Next, run python3 scripts/bootstrap-project-context.py, then have Claude/Codex follow .agent/workflows/adapt-rules.md."
fi
echo "One-time setup: restart the agent session so new skills are discovered, and approve project hooks on first use (Claude: settings approval; Codex: trust .codex and review via /hooks). Hooks are inert until trusted."
