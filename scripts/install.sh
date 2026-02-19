#!/bin/bash
# 安装 AIDD skills 到 agents/codex skills 目录。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

SKILLS_DIRS=(
  "$HOME/.config/agents/skills"
  "$HOME/.agents/skills"
)

TARGET_DIR=""
for dir in "${SKILLS_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    TARGET_DIR="$dir"
    break
  fi
done

if [ -z "$TARGET_DIR" ]; then
  TARGET_DIR="${SKILLS_DIRS[0]}"
  mkdir -p "$TARGET_DIR"
fi

echo "Installing AIDD skills to: $TARGET_DIR"
echo

installed=0
skipped=0

for skill_dir in "$PROJECT_ROOT"/skills/*; do
  [ -d "$skill_dir" ] || continue
  [ -f "$skill_dir/SKILL.md" ] || continue

  skill_name="$(basename "$skill_dir")"
  target_link="$TARGET_DIR/$skill_name"

  skill_dir_abs="$(cd "$skill_dir" && pwd)"
  if [ -L "$target_link" ]; then
    current_link="$(readlink "$target_link")"
    if [ "$current_link" = "$skill_dir_abs" ] || [ "$current_link" = "$skill_dir" ]; then
      echo "  - Skip $skill_name (already linked)"
      skipped=$((skipped + 1))
      continue
    fi
  fi

  if [ -e "$target_link" ] || [ -L "$target_link" ]; then
    backup_path="$target_link.backup.$(date +%Y%m%d_%H%M%S)"
    echo "  - Backup existing $skill_name -> $(basename "$backup_path")"
    mv "$target_link" "$backup_path"
  fi

  ln -s "$skill_dir_abs" "$target_link"
  echo "  + Linked $skill_name"
  installed=$((installed + 1))
done

echo

echo "Installation complete."
echo "  installed: $installed"
echo "  skipped:   $skipped"
echo
echo "Shell setup:"
echo "  export AIDD_ROOT=$PROJECT_ROOT"
echo
echo "After restart, verify with:"
echo "  /skill:aidd-core"
echo "  /skill:idea-new"
