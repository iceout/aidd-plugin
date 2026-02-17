---
schema: aidd.loop_pack.v1
updated_at: <UTC>
ticket: <ABC-123>
work_item_id: <I1>
work_item_key: <iteration_id=I1>
scope_key: <iteration_id_I1>
boundaries:
  allowed_paths:
    - src/feature/**
  forbidden_paths: []
commands_required:
  - <doc/ref or command>
tests_required:
  - <test command>
evidence_policy: RLM-first
---

# Loop Pack — <ABC-123> / <iteration_id=I1>

## Work item
- work_item_id: <I1>
- work_item_key: <iteration_id=I1>
- scope_key: <iteration_id_I1>
- goal: <1–2 sentences>

## Read policy
- Prefer excerpts; read the full Tasklist/PRD/Plan/Research/Spec only if the excerpt lacks **Goal / DoD / Boundaries / Expected paths / Size budget / Tests / Acceptance** or if REVISE explicitly requests more context.

## Boundaries
- allowed_paths:
  - src/feature/**
- forbidden_paths: []

## Commands required
- <doc/ref or command>

## Tests required
- <test command>

## Work item excerpt (required)
> Must cover Goal, DoD, Boundaries, Expected paths, Size budget, Tests, and Acceptance.
