# Stage Lexicon (AIDD)

This document records the canonical vocabulary of stages used by both the workflow SKILLs and the runtime gates.

## Public stages (user-facing)
- `idea`
- `research`
- `plan`
- `review-spec`
- `spec-interview` (optional)
- `tasklist`
- `implement`
- `review`
- `qa`
- `status`

## Internal stages (runtime/internal gates)
- `review-plan`
- `review-prd`

## Legacy aliases (normalized to canonical stages)
- `spec` -> `spec-interview`
- `tasks`/`task` -> `tasklist`

## Mapping rules
- `review-spec` is an umbrella stage that runs the following in order:
  - first `review-plan`
  - then `review-prd`
- Use `review-spec` in user-facing docs and prompts unless you need to reference a specific gate.
- Inside the runtime/gates layer you may refer directly to `review-plan` and `review-prd` when you need the finer detail.

## Artifact expectations (summary)
- Every stage reads/writes inside the workspace tree `aidd/**` (no cross-repo access).
- Planning flow (`idea/research/plan/review-spec/spec-interview/tasklist`) creates/updates docs:
  - `aidd/docs/prd/<ticket>.prd.md`
  - `aidd/docs/research/<ticket>.md`
  - `aidd/docs/plan/<ticket>.md`
  - `aidd/docs/tasklist/<ticket>.md`
- Loop flow (`implement/review/qa/status`) relies on reports:
  - `aidd/reports/loops/**`
  - `aidd/reports/reviewer/**`
  - `aidd/reports/qa/**`
  - `aidd/reports/actions/**`

## Path policy
- Stage-specific entrypoints live under `skills/<stage>/scripts/*`.
- Shared entrypoints live under `skills/aidd-core/runtime/*.py`.
- `tools/*.sh` wrappers are only allowed as temporary redirects during the migration window.
