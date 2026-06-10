#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rules_root="$(cd "$script_dir/.." && pwd)"
template_dir="$rules_root/templates/project"

target=""
dry_run=0

usage() {
  cat <<EOF
Usage: uninstall-rules.sh --target <project-root> [--dry-run]

Lossless uninstall. Nothing is deleted, only moved:
  1. Every kit-managed path is moved into .rules-kit/backups/rules-uninstall-<timestamp>/.
  2. Files you had before the first install are restored from the earliest
     rules-install-* backup.
  3. Files in the uninstall backup that carry your content (adapted project
     facts, your own files inside kit directories) are listed for review —
     take back what you still need.
.rules-kit/ itself is kept; delete it yourself once you are satisfied.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      target="${2:-}"
      shift 2
      ;;
    --dry-run)
      dry_run=1
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
target="$(cd "$target" && pwd)"

if [[ ! -f "$target/.agent/rules-kit.json" ]]; then
  echo "No Relay Rules install found ($target/.agent/rules-kit.json missing)." >&2
  echo "For a broken or partial install, follow the manual uninstall steps in the README." >&2
  exit 1
fi

# Same list the installer records as managedPaths. scripts/ holds the user's
# own files too, so only the three kit scripts are listed, never the directory.
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

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="$target/.rules-kit/backups/rules-uninstall-$timestamp"
earliest="$(find "$target/.rules-kit/backups" -maxdepth 1 -type d -name 'rules-install-*' 2>/dev/null | sort | head -n1)"

echo "Uninstalling Relay Rules from $target"

# 1. Move every managed path into the uninstall backup.
moved=()
for path in "${managed_paths[@]}"; do
  if [[ -e "$target/$path" ]]; then
    if [[ "$dry_run" -eq 1 ]]; then
      echo "[dry-run] move $path -> $backup_dir/$path"
    else
      mkdir -p "$(dirname "$backup_dir/$path")"
      mv "$target/$path" "$backup_dir/$path"
    fi
    moved+=("$path")
  fi
done
if [[ "$dry_run" -ne 1 ]]; then
  rmdir "$target/scripts" 2>/dev/null || true
fi

# 2. Restore what existed before the first install.
if [[ -n "$earliest" ]]; then
  if [[ "$dry_run" -eq 1 ]]; then
    echo "[dry-run] restore your pre-install files from $earliest"
  else
    cp -R "$earliest"/. "$target"/
    echo "Restored your pre-install files from $earliest:"
    (cd "$earliest" && find . -type f ! -path '*/__pycache__/*' ! -name '*.pyc' | sed 's|^\./|  - |')
  fi
else
  echo "No rules-install-* backup found; nothing predated the install (or it was installed with --no-backup)."
fi

if [[ "$dry_run" -eq 1 ]]; then
  echo "[dry-run] list backup files that carry your content (adapted or not from the kit)"
  exit 0
fi

# 3. Everything is preserved in the backup; flag the files that carry the
# user's content. A file identical to the current kit template is safe to
# forget; anything else is either adapted project facts or the user's own.
review=()
while IFS= read -r file; do
  rel="${file#"$backup_dir"/}"
  case "$rel" in
    */__pycache__/*|*.pyc|.agent/rules-kit.json) continue ;;
  esac
  tpl_rel="$rel"
  case "$rel" in
    .agents/skills/*) tpl_rel=".claude/skills/${rel#.agents/skills/}" ;;
    .claude/settings.json) tpl_rel=".claude/settings.example.json" ;;
    .codex/hooks.json) tpl_rel=".codex/hooks.example.json" ;;
  esac
  if [[ -f "$template_dir/$tpl_rel" ]]; then
    cmp -s "$file" "$template_dir/$tpl_rel" || review+=("$rel  (kit file, but its content differs from the current template — likely adapted project facts)")
  else
    review+=("$rel  (not shipped by the kit — your own file)")
  fi
done < <(find "$backup_dir" -type f)

echo ""
echo "Relay Rules uninstalled. Nothing was deleted: everything is in"
echo "  $backup_dir"
if [[ ${#review[@]} -gt 0 ]]; then
  echo ""
  echo "These backed-up files carry your content — copy back what you still need:"
  printf '  - %s\n' "${review[@]}"
fi
echo ""
echo "Once you are satisfied, delete $target/.rules-kit/ yourself to finish."
