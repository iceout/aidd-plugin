#!/bin/bash
# 安装 AIDD skills 到 Kimi skills 目录

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Kimi skills 目录优先级
SKILLS_DIRS=(
    "$HOME/.config/agents/skills"
    "$HOME/.agents/skills"
    "$HOME/.kimi/skills"
)

# 找到第一个存在的 skills 目录
TARGET_DIR=""
for dir in "${SKILLS_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        TARGET_DIR="$dir"
        break
    fi
done

# 如果没有，创建默认目录
if [ -z "$TARGET_DIR" ]; then
    TARGET_DIR="${SKILLS_DIRS[0]}"
    mkdir -p "$TARGET_DIR"
fi

echo "Installing AIDD skills to: $TARGET_DIR"
echo ""

# 为每个 skill 创建符号链接
for skill_dir in "$PROJECT_ROOT"/skills/*/; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        target_link="$TARGET_DIR/$skill_name"
        
        # 如果已存在，备份
        if [ -e "$target_link" ]; then
            echo "  ℹ Backing up existing $skill_name"
            mv "$target_link" "$target_link.backup.$(date +%Y%m%d_%H%M%S)"
        fi
        
        # 创建符号链接
        ln -s "$skill_dir" "$target_link"
        echo "  ✓ Linked $skill_name"
    fi
done

echo ""
echo "Installation complete!"
echo ""
echo "Add to your shell profile (.bashrc/.zshrc):"
echo "  export KIMI_AIDD_ROOT=$PROJECT_ROOT"
echo ""
echo "Then restart Kimi Code CLI and test with:"
echo "  /skill:aidd-core"
