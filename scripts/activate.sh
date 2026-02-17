#!/bin/bash
# 激活开发环境

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
echo "$SCRIPT_DIR"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
echo "$PROJECT_ROOT"

source "$PROJECT_ROOT/.venv/bin/activate"
export AIDD_ROOT="$PROJECT_ROOT"
export PATH="$PROJECT_ROOT/scripts:$PATH"

echo "AIDD dev environment activated (Python 3.13)"
echo "AIDD_ROOT=$AIDD_ROOT"
echo ""
echo "Available commands:"
echo "  ./scripts/test.sh     - Run test suite"
echo "  ./scripts/install.sh  - Install skills to Cursor/Codex/Kimi "
