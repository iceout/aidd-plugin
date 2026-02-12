#!/bin/bash
# 运行测试套件

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"
source .venv/bin/activate

echo "========================================="
echo "Running AIDD Plugin Test Suite"
echo "========================================="
echo ""

# 代码格式检查
echo "=== Running black (format check) ==="
black --check runtime/ 2>/dev/null || {
    echo "⚠ Format issues found. Run 'black runtime/' to fix."
}
echo ""

echo "=== Running ruff (lint check) ==="
ruff check runtime/ 2>/dev/null || {
    echo "⚠ Lint issues found."
}
echo ""

# 类型检查
echo "=== Running mypy (type check) ==="
mypy runtime/aidd_runtime/ 2>/dev/null || {
    echo "⚠ Type check issues found."
}
echo ""

# 单元测试
echo "=== Running pytest ==="
if [ -d "tests" ] && [ "$(ls -A tests/*.py 2>/dev/null)" ]; then
    pytest tests/ -v --cov=runtime/aidd_runtime --cov-report=term-missing 2>/dev/null || {
        echo "⚠ Some tests failed."
    }
else
    echo "ℹ No tests found yet. Create tests in tests/ directory."
fi

echo ""
echo "========================================="
echo "Test suite complete"
echo "========================================="
