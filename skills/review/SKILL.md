---
name: review
description: Review changes, produce findings, and derive follow-up tasks.
argument-hint: $1 [note...]
lang: en
model: inherit
disable-model-invocation: true
user-invocable: true
---

Follow `aidd-core` and `aidd-loop`.

## Steps
1. Resolve active `<ticket>/<scope_key>` for review stage.
2. Mandatory preflight: `python3 ${AIDD_ROOT}/skills/aidd-loop/runtime/preflight_prepare.py`.
3. Read order: readmap -> loop pack -> latest review pack (if any) -> rolling context pack.
4. Run subagent `reviewer`.
5. Generate review artifacts and validate actions via `python3 ${AIDD_ROOT}/skills/review/runtime/review_run.py`.
6. Postflight apply: `python3 ${AIDD_ROOT}/skills/aidd-docio/runtime/actions_apply.py`.
7. Return review contract, findings summary, and next action.

## Command contracts
### `python3 ${AIDD_ROOT}/skills/review/runtime/review_run.py`
- When: canonical review runtime before postflight.
- Inputs: ticket/scope/work-item context and findings/actions payload.
- Outputs: validated review artifacts and stage summary.
- Failure mode: exits non-zero when contracts or prerequisites fail.
- Next action: fix findings/actions and rerun.

## Additional resources
- [CONTRACT.yaml](CONTRACT.yaml)
