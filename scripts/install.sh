#!/bin/bash
# 安装 AIDD skills 到 Kimi/Codex/Cursor skills 目录。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

SUPPORTED_TARGETS=(
  "$HOME/.config/agents/skills"   # Kimi / agents
  "$HOME/.codex/skills"           # Codex
  "$HOME/.cursor/skills"          # Cursor
)

DEFAULT_TARGET="$HOME/.config/agents/skills"

usage() {
  cat <<'EOF'
Usage: ./scripts/install.sh [--target DIR]... [--ide kimi|codex|cursor]

Behavior:
  - default: install into all existing supported dirs
  - if none exists: create ~/.config/agents/skills and install there
  - --target can be repeated to install into explicit dirs only
EOF
}

IDE_TO_TARGET_kimi="$HOME/.config/agents/skills"
IDE_TO_TARGET_codex="$HOME/.codex/skills"
IDE_TO_TARGET_cursor="$HOME/.cursor/skills"

TARGETS=()
EXPLICIT_TARGETS=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      if [ "$#" -lt 2 ]; then
        echo "missing value for --target" >&2
        exit 2
      fi
      TARGETS+=("$2")
      EXPLICIT_TARGETS=1
      shift 2
      ;;
    --ide)
      if [ "$#" -lt 2 ]; then
        echo "missing value for --ide" >&2
        exit 2
      fi
      ide="$(printf '%s' "$2" | tr '[:upper:]' '[:lower:]')"
      case "$ide" in
        kimi) TARGETS+=("$IDE_TO_TARGET_kimi") ;;
        codex) TARGETS+=("$IDE_TO_TARGET_codex") ;;
        cursor) TARGETS+=("$IDE_TO_TARGET_cursor") ;;
        *)
          echo "unsupported ide: $2" >&2
          exit 2
          ;;
      esac
      EXPLICIT_TARGETS=1
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ "$EXPLICIT_TARGETS" -eq 0 ]; then
  for dir in "${SUPPORTED_TARGETS[@]}"; do
    if [ -d "$dir" ]; then
      TARGETS+=("$dir")
    fi
  done
  if [ "${#TARGETS[@]}" -eq 0 ]; then
    TARGETS=("$DEFAULT_TARGET")
  fi
fi

# De-duplicate targets while preserving order.
UNIQ_TARGETS=()
for dir in "${TARGETS[@]-}"; do
  seen=0
  for existing in "${UNIQ_TARGETS[@]-}"; do
    if [ "$existing" = "$dir" ]; then
      seen=1
      break
    fi
  done
  if [ "$seen" -eq 0 ]; then
    UNIQ_TARGETS+=("$dir")
  fi
done

total_installed=0
total_skipped=0
total_backed_up=0

install_into_target() {
  local target_dir="$1"
  local installed=0
  local skipped=0
  local backed_up=0

  mkdir -p "$target_dir"
  echo "Installing AIDD skills to: $target_dir"

  for skill_dir in "$PROJECT_ROOT"/skills/*; do
    [ -d "$skill_dir" ] || continue
    [ -f "$skill_dir/SKILL.md" ] || continue

    local skill_name
    local target_link
    local skill_dir_abs
    skill_name="$(basename "$skill_dir")"
    target_link="$target_dir/$skill_name"
    skill_dir_abs="$(cd "$skill_dir" && pwd)"

    if [ -L "$target_link" ]; then
      local current_link
      current_link="$(readlink "$target_link")"
      if [ "$current_link" = "$skill_dir_abs" ] || [ "$current_link" = "$skill_dir" ]; then
        echo "  - Skip $skill_name (already linked)"
        skipped=$((skipped + 1))
        continue
      fi
    fi

    if [ -e "$target_link" ] || [ -L "$target_link" ]; then
      local backup_path
      backup_path="$target_link.backup.$(date +%Y%m%d_%H%M%S)"
      echo "  - Backup existing $skill_name -> $(basename "$backup_path")"
      mv "$target_link" "$backup_path"
      backed_up=$((backed_up + 1))
    fi

    ln -s "$skill_dir_abs" "$target_link"
    echo "  + Linked $skill_name"
    installed=$((installed + 1))
  done

  echo "  summary: installed=$installed skipped=$skipped backups=$backed_up"
  echo
  total_installed=$((total_installed + installed))
  total_skipped=$((total_skipped + skipped))
  total_backed_up=$((total_backed_up + backed_up))
}

for dir in "${UNIQ_TARGETS[@]}"; do
  install_into_target "$dir"
done

echo "Installation complete."
echo "  targets:   ${#UNIQ_TARGETS[@]}"
echo "  installed: $total_installed"
echo "  skipped:   $total_skipped"
echo "  backups:   $total_backed_up"
echo
echo "Shell setup:"
echo "  export AIDD_ROOT=$PROJECT_ROOT"
echo
echo "After restart, verify with:"
echo "  ./scripts/verify-flows.sh"
