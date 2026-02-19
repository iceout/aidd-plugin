---
name: tasks-new
description: Create or refine tasklist from PRD/plan/spec and validate tasklist contract.
argument-hint: $1 [note...]
lang: en
model: inherit
disable-model-invocation: true
user-invocable: true
---

Follow `aidd-core`.

## Steps
1. Set active stage: `tasklist`; sync active feature.
2. Run: `python3 ${AIDD_ROOT}/skills/tasks-new/runtime/tasks_new.py --ticket <ticket>`.
3. Run PRD gate: `python3 ${AIDD_ROOT}/skills/aidd-flow-state/runtime/prd_check.py --ticket <ticket>`.
4. Build/update rolling context pack.
5. Run subagent `tasklist-refiner`.
6. Validate tasklist: `python3 ${AIDD_ROOT}/skills/aidd-flow-state/runtime/tasklist_check.py --ticket <ticket>`.
7. Return output contract and next step `/skill:implement <ticket>`.

## Command contracts
### `python3 ${AIDD_ROOT}/skills/tasks-new/runtime/tasks_new.py`
- When: canonical tasklist-stage entrypoint.
- Inputs: `--ticket <ticket>` (optional `--tasklist`, `--force-template`, `--strict`).
- Outputs: initialized/synced tasklist and validation summary.
- Failure mode: exits non-zero when source artifacts or tasklist contract are invalid.
- Next action: fix blockers and rerun.

## Notes
- Planning stage: `AIDD:ACTIONS_LOG: n/a`.

## Additional resources
- [templates/tasklist.template.md](templates/tasklist.template.md)
