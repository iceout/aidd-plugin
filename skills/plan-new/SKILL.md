---
name: plan-new
description: Build implementation plan from PRD and research artifacts.
argument-hint: $1 [note...]
lang: en
model: inherit
disable-model-invocation: true
user-invocable: true
---

Follow `aidd-core`.

## Steps
1. Set active stage: `plan`; ensure active feature is current.
2. Run research gate: `python3 ${AIDD_ROOT}/skills/plan-new/runtime/research_check.py --ticket <ticket>`.
3. Run PRD gate: `python3 ${AIDD_ROOT}/skills/aidd-flow-state/runtime/prd_check.py --ticket <ticket>`.
4. Build/update rolling context pack.
5. Run subagents in order: `planner`, then `validator`.
6. Update `aidd/docs/plan/<ticket>.md` and output stage contract.

## Command contracts
### `python3 ${AIDD_ROOT}/skills/plan-new/runtime/research_check.py`
- When: before planning.
- Inputs: `--ticket <ticket>` (optional `--branch`).
- Outputs: deterministic research-readiness verdict.
- Failure mode: exits non-zero when research artifacts/status are not ready.
- Next action: resolve research blockers then rerun.

## Notes
- Planning stage: `AIDD:ACTIONS_LOG: n/a`.

## Additional resources
- [templates/plan.template.md](templates/plan.template.md)
