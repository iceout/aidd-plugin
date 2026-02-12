#!/bin/bash
# 激活开发环境

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

source "$PROJECT_ROOT/.venv/bin/activate"
export KIMI_AIDD_ROOT="$PROJECT_ROOT"
export PATH="$PROJECT_ROOT/scripts:$PATH"

echo "AIDD dev environment activated (Python 3.13)"
echo "KIMI_AIDD_ROOT=$KIMI_AIDD_ROOT"
echo ""
echo "Available commands:"
echo "  ./scripts/test.sh     - Run test suite"
echo "  ./scripts/install.sh  - Install skills to Kimi"
