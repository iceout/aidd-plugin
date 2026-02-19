---
name: qa
description: Run QA checks and produce QA report artifacts.
argument-hint: $1 [note...]
lang: en
model: inherit
disable-model-invocation: true
user-invocable: true
---

Follow `aidd-core` and `aidd-loop`.

## Steps
1. Resolve active `<ticket>/<scope_key>` for QA stage.
2. Mandatory preflight: `python3 ${AIDD_ROOT}/skills/aidd-loop/runtime/preflight_prepare.py`.
3. Read order: readmap -> loop pack -> latest review pack (if any) -> rolling context pack.
4. Run subagent `qa`.
5. Run QA and validate actions via `python3 ${AIDD_ROOT}/skills/qa/runtime/qa.py` and `qa_run.py`.
6. Postflight apply: `python3 ${AIDD_ROOT}/skills/aidd-docio/runtime/actions_apply.py`.
7. Return QA contract with report paths and explicit next action.

## Command contracts
### `python3 ${AIDD_ROOT}/skills/qa/runtime/qa_run.py`
- When: canonical QA runtime before postflight.
- Inputs: ticket/scope/work-item context, findings, and actions payload.
- Outputs: validated QA artifacts and stage summary.
- Failure mode: exits non-zero when report/actions contracts fail.
- Next action: fix blockers and rerun.

## Additional resources
- [CONTRACT.yaml](CONTRACT.yaml)
