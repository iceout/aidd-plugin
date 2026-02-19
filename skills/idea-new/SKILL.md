---
name: idea-new
description: Start a feature by setting active ticket/stage, drafting PRD, and collecting missing Q&A.
argument-hint: $1 [note...]
lang: en
model: inherit
disable-model-invocation: true
user-invocable: true
---

Follow `aidd-core`.

## Steps
1. Resolve `<ticket>` and parse idea note from user input.
2. Set active stage: `python3 ${AIDD_ROOT}/skills/aidd-flow-state/runtime/set_active_stage.py idea`.
3. Set active feature: `python3 ${AIDD_ROOT}/skills/aidd-flow-state/runtime/set_active_feature.py <ticket>`.
4. Run gate: `python3 ${AIDD_ROOT}/skills/idea-new/runtime/analyst_check.py --ticket <ticket>`.
5. Run subagent `analyst` to update `aidd/docs/prd/<ticket>.prd.md`.
6. If answers were added, rerun `analyst_check.py` and sync readiness.
7. Return open questions (if any) and next step `/skill:researcher <ticket>`.

## Command contracts
### `python3 ${AIDD_ROOT}/skills/idea-new/runtime/analyst_check.py`
- When: before and after analyst updates.
- Inputs: `--ticket <ticket>` (optional `--branch`, `--allow-blocked`, `--no-ready-required`).
- Outputs: deterministic analyst readiness result.
- Failure mode: exits non-zero when PRD status/questions violate gate policy.
- Next action: fix PRD/QA sections, then rerun.

## Notes
- Use aidd-core question format.
- Planning stage: `AIDD:ACTIONS_LOG: n/a`.

## Additional resources
- [templates/prd.template.md](templates/prd.template.md)
