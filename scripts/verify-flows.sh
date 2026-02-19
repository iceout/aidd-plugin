#!/bin/bash
# 验证 AIDD Skills 是否正确安装。

set -euo pipefail

TARGET_DIR="${HOME}/.config/agents/skills"
if [ ! -d "$TARGET_DIR" ]; then
  echo "skills dir not found: $TARGET_DIR"
  exit 1
fi

echo "=== AIDD Skills Verification ==="
echo "target: $TARGET_DIR"
echo

echo "Installed skill dirs (with SKILL.md):"
find "$TARGET_DIR" -mindepth 1 -maxdepth 1 -type d | while read -r d; do
  if [ -f "$d/SKILL.md" ]; then
    echo "  + $(basename "$d")"
  fi
done

echo
required=(
  aidd-core
  aidd-init-flow
  idea-new
  researcher
  plan-new
  review-spec
  spec-interview
  tasks-new
  implement
  review
  qa
)

missing=0
for s in "${required[@]}"; do
  if [ ! -f "$TARGET_DIR/$s/SKILL.md" ]; then
    echo "  ! missing: $s"
    missing=$((missing + 1))
  fi
done

echo
if [ "$missing" -eq 0 ]; then
  echo "All required stage skills are installed."
else
  echo "Missing required skills: $missing"
  exit 2
fi

echo
echo "Legacy flow aliases (optional):"
for s in aidd-idea-flow aidd-research-flow aidd-plan-flow aidd-implement-flow aidd-review-flow aidd-qa-flow; do
  if [ -f "$TARGET_DIR/$s/SKILL.md" ]; then
    echo "  + $s"
  fi
done
