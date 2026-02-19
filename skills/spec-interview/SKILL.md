---
name: spec-interview
description: Run spec interview and sync spec.yaml from confirmed answers.
argument-hint: $1 [note...]
lang: en
model: inherit
disable-model-invocation: true
user-invocable: true
---

Follow `aidd-core`.

## Steps
1. Set active stage `spec-interview` and sync active feature.
2. Run: `python3 ${AIDD_ROOT}/skills/spec-interview/runtime/spec_interview.py --ticket <ticket>`.
3. Ask only missing spec questions and update `aidd/docs/spec/<ticket>.spec.yaml`.
4. Sync confirmed answers into `AIDD:OPEN_QUESTIONS` and `AIDD:DECISIONS` as needed.
5. Return output contract and next step `/skill:tasks-new <ticket>`.

## Command contracts
### `python3 ${AIDD_ROOT}/skills/spec-interview/runtime/spec_interview.py`
- When: canonical spec-interview entrypoint.
- Inputs: `--ticket <ticket>` with optional `--spec` path override.
- Outputs: initialized/synced spec artifact and stage status.
- Failure mode: exits non-zero when required artifacts are missing or spec contract is invalid.
- Next action: collect missing answers and rerun.

## Additional resources
- [templates/spec.template.yaml](templates/spec.template.yaml)
