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
upgrade=0

usage() {
  cat <<EOF
Usage: install-rules.sh --target <project-root> [options]

Options:
  --target <path>   Project root to install into.
  --force           Replace existing rule files after backing them up.
  --upgrade         Refresh kit machinery (scripts, hooks, skills, workflows,
                    .agent/index.md, example configs) on an existing install.
                    Never touches agent-adapted content. Mutually exclusive
                    with --force.
  --no-backup       Do not back up existing files. Requires --force.
  --dry-run         Print planned actions without writing.
  --bootstrap       Scan project files after install and generate review candidates for agent adaptation.
  -h, --help        Show this help.

Default behavior:
  - Refuses to overwrite existing rule files unless --force or --upgrade is provided.
  - Backs up existing rule files to .rules-kit/backups/rules-install-<timestamp>/.
  - --upgrade backs up every replaced path to .rules-kit/backups/rules-upgrade-<timestamp>/.
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
    --upgrade)
      upgrade=1
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

if [[ "$upgrade" -eq 1 && "$force" -eq 1 ]]; then
  echo "--upgrade and --force are mutually exclusive: --force factory-resets everything, --upgrade refreshes kit machinery only." >&2
  exit 2
fi

if [[ "$upgrade" -eq 1 && "$bootstrap" -eq 1 ]]; then
  echo "--upgrade does not take --bootstrap: bootstrap regenerates scan blocks inside agent-adapted docs and is for fresh installs." >&2
  exit 2
fi

if [[ ! -d "$target" ]]; then
  if [[ "$upgrade" -eq 1 ]]; then
    echo "--upgrade requires an existing install, but the target directory does not exist: $target" >&2
    exit 1
  fi
  if ! mkdir -p "$target"; then
    echo "Cannot create target directory: $target" >&2
    exit 1
  fi
fi

target="$(cd "$target" && pwd)"

if [[ ! -d "$template_dir" ]]; then
  echo "Template directory not found: $template_dir" >&2
  exit 1
fi

if ! git -C "$target" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "WARNING: $target is not inside a git work tree; drift detection and candidate scanning depend on git and stay inert until you run 'git init'."
fi

if [[ "$upgrade" -eq 1 && ! -f "$target/.agent/rules-kit.json" ]]; then
  echo "--upgrade requires an existing Rules install: $target/.agent/rules-kit.json not found." >&2
  echo "Run a plain install first (install-rules.sh --target <path> --bootstrap), or --force to replace a broken one." >&2
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

managed_paths_json="["
for path in "${managed_paths[@]}"; do
  managed_paths_json+="\"$path\", "
done
managed_paths_json="${managed_paths_json%, }]"

existing=()
for path in "${managed_paths[@]}"; do
  if [[ -e "$target/$path" ]]; then
    existing+=("$path")
  fi
done

if [[ "$upgrade" -ne 1 && ${#existing[@]} -gt 0 && "$force" -ne 1 ]]; then
  echo "Existing rule paths found in $target:" >&2
  printf '  - %s\n' "${existing[@]}" >&2
  echo "Re-run with --force to back them up and replace them, or --upgrade to refresh kit machinery while keeping adapted content." >&2
  exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
metadata="$target/.agent/rules-kit.json"

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

if [[ "$upgrade" -eq 1 ]]; then
  backup_dir="$target/.rules-kit/backups/rules-upgrade-$timestamp"
  echo "Upgrading Relay Rules tooling to $version in $target"

  # Kit machinery only. Agent-adapted content (.agent/product-invariants.md,
  # user-journeys.md, command-contract.md, drift-map.yml, adaptation-review.md,
  # domains/, rule-candidates.md, AGENTS.md, CLAUDE.md, .claude/rules/, and the
  # active .claude/settings.json / .codex/hooks.json) is never touched.
  upgrade_paths=(
    "scripts/check-doc-drift.py"
    "scripts/bootstrap-project-context.py"
    "scripts/suggest-rule-updates.py"
    ".agent/index.md"
    ".claude/settings.example.json"
    ".codex/hooks.example.json"
  )
  for file in "$template_dir/.claude/hooks/"*.py; do
    upgrade_paths+=(".claude/hooks/$(basename "$file")")
  done
  for file in "$template_dir/.codex/hooks/"*.py; do
    upgrade_paths+=(".codex/hooks/$(basename "$file")")
  done
  for dir in "$template_dir/.claude/skills/"*/; do
    upgrade_paths+=(".claude/skills/$(basename "$dir")")
  done
  for file in "$template_dir/.agent/workflows/"*.md; do
    upgrade_paths+=(".agent/workflows/$(basename "$file")")
  done

  # Kit files that older versions shipped under names this version no longer
  # uses. Without cleanup the old and new variants coexist after an upgrade
  # (e.g. skills/review next to skills/review-changes). Kit machinery only —
  # never list adapted content here.
  obsolete_paths=(
    ".claude/skills/review"       # renamed to review-changes
    ".claude/skills/drift-check"  # removed; doc-drift covers it
  )

  if [[ "$dry_run" -eq 1 ]]; then
    echo "[dry-run] back up replaced paths to $backup_dir"
    printf '[dry-run] replace %s\n' "${upgrade_paths[@]}"
    for path in "${obsolete_paths[@]}"; do
      [[ -e "$target/$path" ]] && echo "[dry-run] remove obsolete kit path $path (backed up first)"
    done
    echo "[dry-run] regenerate .agents/skills from canonical .claude/skills"
    echo "[dry-run] update $metadata (new rulesKitVersion, upgradedAt, managedPaths; installedAt preserved)"
  else
    echo "Backing up replaced kit paths to $backup_dir"
    mkdir -p "$backup_dir"
    for path in "${upgrade_paths[@]}"; do
      if [[ -e "$target/$path" ]]; then
        mkdir -p "$(dirname "$backup_dir/$path")"
        cp -R "$target/$path" "$backup_dir/$path"
        rm -rf "$target/$path"
      fi
      mkdir -p "$(dirname "$target/$path")"
      cp -R "$template_dir/$path" "$target/$path"
    done
    for path in "${obsolete_paths[@]}"; do
      if [[ -e "$target/$path" ]]; then
        mkdir -p "$(dirname "$backup_dir/$path")"
        cp -R "$target/$path" "$backup_dir/$path"
        rm -rf "$target/$path"
        echo "Removed obsolete kit path $path (backup: $backup_dir/$path)"
      fi
    done
    # .claude/skills is the canonical tree; regenerate the Codex tree exactly
    # like a fresh install so the two cannot drift apart.
    if [[ -d "$target/.agents/skills" ]]; then
      mkdir -p "$backup_dir/.agents"
      cp -R "$target/.agents/skills" "$backup_dir/.agents/skills"
    fi
    rm -rf "$target/.agents/skills"
    mkdir -p "$target/.agents"
    cp -R "$target/.claude/skills" "$target/.agents/skills"
    find "$target/.claude" "$target/.codex" "$target/.agents" "$target/scripts" \
      -path '*/__pycache__*' -prune -exec rm -rf {} + 2>/dev/null || true
    chmod +x "$target/scripts/check-doc-drift.py" \
      "$target/scripts/bootstrap-project-context.py" \
      "$target/scripts/suggest-rule-updates.py" \
      "$target/.codex/hooks/"*.py \
      "$target/.claude/hooks/"*.py 2>/dev/null || true
  fi

  # Structure that newer kit versions require but older installs predate.
  # Only seeded when missing; existing files are never touched. Pointer globs
  # are mirrored from the project's own drift-map (template globs as fallback)
  # so on-demand loading works without waiting for re-adaptation.
  if [[ "$dry_run" -eq 1 ]]; then
    for file in "$template_dir/.claude/rules/"*.md; do
      rel=".claude/rules/$(basename "$file")"
      [[ -e "$target/$rel" ]] || echo "[dry-run] seed $rel (globs mirrored from .agent/drift-map.yml when available)"
    done
    [[ -f "$target/.claude/settings.json" ]] || echo "[dry-run] seed .claude/settings.json from .claude/settings.example.json"
    [[ -f "$target/.codex/hooks.json" ]] || echo "[dry-run] seed .codex/hooks.json from .codex/hooks.example.json"
  else
    seeded=()
    for file in "$template_dir/.claude/rules/"*.md; do
      rel=".claude/rules/$(basename "$file")"
      if [[ ! -e "$target/$rel" ]]; then
        mkdir -p "$target/.claude/rules"
        python3 - "$file" "$target/$rel" "$target/.agent/drift-map.yml" <<'PY'
import re
import sys
from pathlib import Path

template = Path(sys.argv[1]).read_text(encoding="utf-8")
out = Path(sys.argv[2])
drift_path = Path(sys.argv[3])
name = out.stem

match = re.match(r"^---\n(.*?)\n---\n(.*)$", template, flags=re.DOTALL)
frontmatter, body = (match.group(1), match.group(2)) if match else ("paths:", template)

# Same minimal parser as scripts/check-doc-drift.py; pull the globs of the
# drift-map rule with the same name as this pointer file.
globs = []
if drift_path.is_file():
    current = None
    active = None
    for raw in drift_path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if re.match(r"^\s*-\s+name:\s*", line):
            current = line.split("name:", 1)[1].strip().strip('"')
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
        if stripped.startswith("- ") and active == "paths" and current == name:
            globs.append(stripped[2:].strip().strip('"'))

if globs:
    frontmatter = "paths:\n" + "\n".join(f'  - "{glob}"' for glob in globs)
out.write_text(f"---\n{frontmatter}\n---\n{body}", encoding="utf-8")
PY
        seeded+=("$rel")
      fi
    done
    if [[ ! -f "$target/.claude/settings.json" && -f "$target/.claude/settings.example.json" ]]; then
      cp "$target/.claude/settings.example.json" "$target/.claude/settings.json"
      seeded+=(".claude/settings.json")
    fi
    if [[ ! -f "$target/.codex/hooks.json" && -f "$target/.codex/hooks.example.json" ]]; then
      cp "$target/.codex/hooks.example.json" "$target/.codex/hooks.json"
      seeded+=(".codex/hooks.json")
    fi
    if [[ ${#seeded[@]} -gt 0 ]]; then
      echo "Seeded structure new to this kit version (missing in the old install):"
      printf '  - %s\n' "${seeded[@]}"
    fi
  fi

  if [[ "$dry_run" -eq 1 ]]; then
    echo "[dry-run] write $metadata"
  else
    installed_at="$(python3 -c 'import json, sys
try:
    value = json.load(open(sys.argv[1])).get("installedAt")
    print(value if isinstance(value, str) else "")
except Exception:
    print("")' "$metadata")"
    if [[ -z "$installed_at" ]]; then
      installed_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    fi
    cat > "$metadata" <<EOF
{
  "rulesKitVersion": "$version",
  "installedAt": "$installed_at",
  "upgradedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source": "$rules_root",
  "template": "templates/project",
  "managedPaths": $managed_paths_json,
  "backup": "$backup_dir"
}
EOF
  fi

  if [[ "$dry_run" -ne 1 ]]; then
    for pair in ".claude/settings.example.json:.claude/settings.json" ".codex/hooks.example.json:.codex/hooks.json"; do
      example_cfg="${pair%%:*}"
      active_cfg="${pair##*:}"
      if [[ -f "$target/$active_cfg" ]] && ! cmp -s "$target/$example_cfg" "$target/$active_cfg"; then
        echo ""
        echo "NOTICE: the refreshed $example_cfg differs from your active $active_cfg."
        echo "  The active config was left untouched. Diff and merge manually:"
        echo "  diff \"$target/$example_cfg\" \"$target/$active_cfg\""
      fi
    done
    # Validation gaps in adapted files (AGENTS.md, CLAUDE.md, .agent/*) are
    # expected when upgrading across versions that added contract content:
    # the upgrade never rewrites adapted files, so an agent must merge the
    # new template content. That is follow-up adaptation work, not a failed
    # upgrade — report it as such instead of dying on the first FAIL.
    if ! bash "$rules_root/scripts/validate-installed-project.sh" "$target"; then
      echo ""
      echo "NOTICE: kit machinery is upgraded, but validation found a gap (FAIL above)."
      echo "  Gaps in adapted files mean they predate this kit version. Have a Claude/Codex"
      echo "  agent merge the new content from $template_dir"
      echo "  into the adapted files (validation names each missing piece), then re-run:"
      echo "  bash $rules_root/scripts/validate-installed-project.sh $target --require-adapted --require-candidates-reviewed"
      echo "  If a FAIL is not about adapted content, treat it as a real installation problem."
    fi
  fi

  echo "Relay Rules tooling upgraded to $version."
  echo "Existing agent-adapted content (.agent docs, drift-map, domains, AGENTS.md, CLAUDE.md, .claude/rules/, active hook configs) was not modified; missing structure was only seeded, never overwritten."
  echo "Backup of replaced kit files: $backup_dir"
  exit 0
fi

backup_dir="$target/.rules-kit/backups/rules-install-$timestamp"

echo "Installing Relay Rules $version into $target"

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

if [[ "$dry_run" -eq 1 ]]; then
  echo "[dry-run] write $metadata"
else
  cat > "$metadata" <<EOF
{
  "rulesKitVersion": "$version",
  "installedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source": "$rules_root",
  "template": "templates/project",
  "managedPaths": $managed_paths_json,
  "backup": $(if [[ ${#existing[@]} -gt 0 && "$backup" -eq 1 ]]; then printf '"%s"' "$backup_dir"; else printf 'null'; fi)
}
EOF
fi

if [[ "$dry_run" -ne 1 ]]; then
  if [[ "$bootstrap" -eq 1 ]]; then
    (cd "$target" && python3 scripts/bootstrap-project-context.py)
    # Day-zero noise control: candidates whose evidence is only the files this
    # installer just wrote are resolved automatically instead of blocking the
    # first Stop on the kit's own paths.
    (cd "$target" && python3 scripts/suggest-rule-updates.py --quiet --resolve-kit-install)
  fi
  bash "$rules_root/scripts/validate-installed-project.sh" "$target"
fi

if [[ "$dry_run" -ne 1 && ${#existing[@]} -gt 0 && "$backup" -eq 1 ]]; then
  for active_cfg in ".claude/settings.json" ".codex/hooks.json"; do
    if [[ -f "$backup_dir/$active_cfg" ]] && ! cmp -s "$backup_dir/$active_cfg" "$target/$active_cfg"; then
      echo ""
      echo "WARNING: --force replaced $active_cfg with the kit default, and your previous version was different."
      echo "  Your old config: $backup_dir/$active_cfg"
      echo "  Merge your custom hooks/permissions back manually:"
      echo "  diff \"$backup_dir/$active_cfg\" \"$target/$active_cfg\""
    fi
  done
  for agent_dir in ".claude" ".codex"; do
    if [[ -d "$backup_dir/$agent_dir" ]]; then
      extra_files="$(cd "$backup_dir/$agent_dir" && find . -type f ! -path '*/__pycache__/*' ! -name '*.pyc' | sed 's|^\./||' | while IFS= read -r file; do
        [[ -e "$target/$agent_dir/$file" ]] || printf '%s/%s\n' "$agent_dir" "$file"
      done)"
      if [[ -n "$extra_files" ]]; then
        echo ""
        echo "WARNING: your previous $agent_dir/ contained files the kit does not ship (custom hook scripts, commands, ...). They were moved into the backup:"
        while IFS= read -r file; do
          echo "  - $backup_dir/$file"
        done <<< "$extra_files"
        echo "  Restore the ones you still need from there."
      fi
    fi
  done
fi

if [[ "$bootstrap" -eq 1 ]]; then
  echo "Relay Rules installed and bootstrapped."
  echo "Status: pending agent adaptation. A Claude/Codex agent must run .agent/workflows/adapt-rules.md and mark .agent/adaptation-review.md as adapted before these are treated as project rules."
else
  echo "Relay Rules installed."
  echo "Status: pending agent adaptation. Next, run python3 scripts/bootstrap-project-context.py, then have Claude/Codex follow .agent/workflows/adapt-rules.md."
fi
echo "One-time setup: restart the agent session so new skills are discovered, and approve project hooks on first use (Claude: settings approval; Codex: trust .codex and review via /hooks). Hooks are inert until trusted."
