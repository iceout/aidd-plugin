---
name: review-spec
description: Review plan + PRD readiness before tasklist generation.
argument-hint: $1 [note...]
lang: en
model: inherit
disable-model-invocation: true
user-invocable: true
---

Follow `aidd-core`.

## Steps
1. Set active stage to `review-plan`, then `review-prd`.
2. Run: `python3 ${AIDD_ROOT}/skills/review-spec/runtime/prd_review_cli.py --ticket <ticket>`.
3. Gate PRD readiness with `python3 ${AIDD_ROOT}/skills/aidd-flow-state/runtime/prd_check.py --ticket <ticket>`.
4. Build rolling context pack and run subagents `plan-reviewer` then `prd-reviewer`.
5. Persist report to `aidd/reports/prd/<ticket>.json`.
6. Return stage contract and next action.

## Command contracts
### `python3 ${AIDD_ROOT}/skills/review-spec/runtime/prd_review_cli.py`
- When: canonical review-spec entrypoint.
- Inputs: `--ticket <ticket>` and active PRD/plan artifacts.
- Outputs: normalized PRD review report and readiness status.
- Failure mode: exits non-zero when inputs/report contract are invalid.
- Next action: fix blockers and rerun.
