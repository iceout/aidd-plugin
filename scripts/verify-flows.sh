#!/bin/bash
# 验证 AIDD Skills 是否在 Kimi/Codex/Cursor 目录中正确安装。

set -euo pipefail

SUPPORTED_TARGETS=(
  "$HOME/.config/agents/skills"
  "$HOME/.codex/skills"
  "$HOME/.cursor/skills"
)

usage() {
  cat <<'EOF'
Usage: ./scripts/verify-flows.sh [--target DIR]...

Behavior:
  - default: verify all existing supported dirs
  - --target can be repeated to verify explicit dirs only
EOF
}

TARGETS=()
EXPLICIT=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      if [ "$#" -lt 2 ]; then
        echo "missing value for --target" >&2
        exit 2
      fi
      TARGETS+=("$2")
      EXPLICIT=1
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

if [ "$EXPLICIT" -eq 0 ]; then
  for dir in "${SUPPORTED_TARGETS[@]}"; do
    if [ -d "$dir" ]; then
      TARGETS+=("$dir")
    fi
  done
fi

if [ "${#TARGETS[@]}" -eq 0 ]; then
  echo "No skills directories found to verify." >&2
  exit 1
fi

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

failed_targets=0

verify_target() {
  local target_dir="$1"
  local missing=0

  echo "=== AIDD Skills Verification ==="
  echo "target: $target_dir"
  echo

  if [ ! -d "$target_dir" ]; then
    echo "skills dir not found: $target_dir"
    echo
    return 1
  fi

  echo "Installed skill dirs (with SKILL.md):"
  find "$target_dir" -mindepth 1 -maxdepth 1 -type d | while read -r d; do
    if [ -f "$d/SKILL.md" ]; then
      echo "  + $(basename "$d")"
    fi
  done

  echo
  for s in "${required[@]}"; do
    if [ ! -f "$target_dir/$s/SKILL.md" ]; then
      echo "  ! missing: $s"
      missing=$((missing + 1))
    fi
  done

  echo
  if [ "$missing" -eq 0 ]; then
    echo "All required stage skills are installed."
  else
    echo "Missing required skills: $missing"
    return 1
  fi

  echo
  echo "Legacy flow aliases (optional):"
  for s in aidd-idea-flow aidd-research-flow aidd-plan-flow aidd-implement-flow aidd-review-flow aidd-qa-flow; do
    if [ -f "$target_dir/$s/SKILL.md" ]; then
      echo "  + $s"
    fi
  done
  echo
  return 0
}

for dir in "${TARGETS[@]}"; do
  if ! verify_target "$dir"; then
    failed_targets=$((failed_targets + 1))
  fi
done

if [ "$failed_targets" -ne 0 ]; then
  echo "Verification failed for $failed_targets target(s)." >&2
  exit 2
fi
