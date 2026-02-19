---
name: implement
description: Implement the next work item with loop discipline.
argument-hint: $1 [note...] [test=fast|targeted|full|none] [tests=<filters>] [tasks=<task1,task2>]
lang: en
model: inherit
disable-model-invocation: true
user-invocable: true
---

Follow `aidd-core` and `aidd-loop`.

## Steps
1. Resolve active `<ticket>/<scope_key>` for implement stage.
2. Mandatory preflight: `python3 ${AIDD_ROOT}/skills/aidd-loop/runtime/preflight_prepare.py`.
3. Read order: readmap -> loop pack -> latest review pack (if any) -> rolling context pack.
4. Run subagent `implementer`.
5. Validate actions with `python3 ${AIDD_ROOT}/skills/implement/runtime/implement_run.py`.
6. Postflight apply: `python3 ${AIDD_ROOT}/skills/aidd-docio/runtime/actions_apply.py`.
7. Run boundary/progress/stage-result/status-summary checks and return stage contract.

## Command contracts
### `python3 ${AIDD_ROOT}/skills/implement/runtime/implement_run.py`
- When: canonical implement runtime before postflight.
- Inputs: ticket/scope/work-item context and actions payload.
- Outputs: validated actions artifact and stage summary.
- Failure mode: exits non-zero when actions schema or prerequisites fail.
- Next action: fix inputs and rerun.

## Additional resources
- [CONTRACT.yaml](CONTRACT.yaml)
