#!/bin/bash
# 运行测试套件（严格模式）。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

if [ ! -f ".venv/bin/activate" ]; then
    echo "virtualenv not found: .venv/bin/activate" >&2
    exit 1
fi

source .venv/bin/activate

require_python_module() {
    local module="$1"
    if ! python -c "import ${module}" >/dev/null 2>&1; then
        echo "missing python module: ${module}. Run ./scripts/install.sh or uv pip sync pyproject.toml." >&2
        exit 1
    fi
}

require_python_module black
require_python_module ruff
require_python_module mypy
require_python_module pytest
require_python_module pytest_cov

echo "========================================="
echo "Running AIDD Plugin Test Suite"
echo "========================================="
echo ""

# 代码格式检查（失败即退出）
echo "=== Running black (format check) ==="
python -m black --check aidd_runtime/ skills/ hooks/ tests/
echo ""

echo "=== Running ruff (lint check, core runtime) ==="
python -m ruff check aidd_runtime/
echo ""

# 类型检查（失败即退出）
echo "=== Running mypy (type check) ==="
python -m mypy aidd_runtime/
echo ""

# 单元测试（失败即退出）
echo "=== Running pytest ==="
if [ -d "tests" ] && [ "$(find tests -name '*.py' -type f | head -n 1)" ]; then
    if [ ! -f ".coveragerc" ]; then
        echo "coverage config not found: .coveragerc" >&2
        exit 1
    fi
    python -m pytest tests/ -v \
        --cov=aidd_runtime \
        --cov=hooks \
        --cov=skills \
        --cov-config=.coveragerc \
        --cov-report=term-missing
else
    echo "No tests found in tests/ directory." >&2
    exit 1
fi

echo ""
echo "========================================="
echo "Test suite complete (strict mode)"
echo "========================================="
