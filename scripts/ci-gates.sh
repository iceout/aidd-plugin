#!/bin/bash
# Run AIDD hooks in CI-friendly mode (Codex/Cursor/Kimi compatible).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

WORKSPACE="$(pwd)"
RUN_WORKFLOW=1
RUN_TESTS=1
RUN_QA=1
QA_ARGS=()

usage() {
  cat <<'EOF'
Usage: ./scripts/ci-gates.sh [options] [-- <qa args>]

Options:
  --workspace DIR      Run gates from DIR (default: current directory)
  --skip-workflow      Skip hooks/gate-workflow.sh
  --skip-tests         Skip hooks/gate-tests.sh
  --skip-qa            Skip hooks/gate-qa.sh
  -h, --help           Show this help

Examples:
  ./scripts/ci-gates.sh --workspace /path/to/repo
  ./scripts/ci-gates.sh --skip-tests -- --skip-tests
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --workspace)
      if [ "$#" -lt 2 ]; then
        echo "missing value for --workspace" >&2
        exit 2
      fi
      WORKSPACE="$2"
      shift 2
      ;;
    --skip-workflow)
      RUN_WORKFLOW=0
      shift
      ;;
    --skip-tests)
      RUN_TESTS=0
      shift
      ;;
    --skip-qa)
      RUN_QA=0
      shift
      ;;
    --)
      shift
      QA_ARGS=("$@")
      break
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

WORKSPACE="$(cd "$WORKSPACE" && pwd)"
export AIDD_ROOT="${AIDD_ROOT:-$PROJECT_ROOT}"

echo "[ci-gates] workspace: $WORKSPACE"
echo "[ci-gates] AIDD_ROOT: $AIDD_ROOT"

if [ "$RUN_WORKFLOW" -eq 1 ]; then
  echo "[ci-gates] run gate-workflow"
  (cd "$WORKSPACE" && python3 "$AIDD_ROOT/hooks/gate-workflow.sh")
fi

if [ "$RUN_TESTS" -eq 1 ]; then
  echo "[ci-gates] run gate-tests"
  (cd "$WORKSPACE" && python3 "$AIDD_ROOT/hooks/gate-tests.sh")
fi

if [ "$RUN_QA" -eq 1 ]; then
  echo "[ci-gates] run gate-qa"
  if [ "${#QA_ARGS[@]}" -gt 0 ]; then
    (cd "$WORKSPACE" && python3 "$AIDD_ROOT/hooks/gate-qa.sh" "${QA_ARGS[@]}")
  else
    (cd "$WORKSPACE" && python3 "$AIDD_ROOT/hooks/gate-qa.sh")
  fi
fi

echo "[ci-gates] done"
