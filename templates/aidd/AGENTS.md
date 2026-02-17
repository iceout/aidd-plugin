# AGENTS

Single entry point for AIDD runtime agents within the workspace. Contributor guidance lives at `AGENTS.md` in the repository root.

## Skill-first canon
- Core policy: `${AIDD_ROOT}/skills/aidd-core/SKILL.md`.
- Loop policy: `${AIDD_ROOT}/skills/aidd-loop/SKILL.md`.
- This document is user-facing; do not duplicate the procedural logic defined inside each SKILL.
- Stage lexicon (public/internal): `aidd/docs/shared/stage-lexicon.md`.

## Baseline rules
- All artifacts must live under `aidd/**` relative to the workspace root.
- For pack-first/read-budget expectations, output contracts, question format, DocOps, and subagent guardrails refer to `skills/aidd-core`.
- `AIDD:READ_LOG` is mandatory whenever artifacts are read and when logging fallback full-read reasons (see `skills/aidd-core`).
- Loop discipline is defined in `skills/aidd-loop`.
- Stage/shared runtime entrypoints live under `skills/*/runtime/*.py` (Python only).
- Shared entrypoints: canonical paths `skills/aidd-core/runtime/*.py`, `skills/aidd-loop/runtime/*.py`, `skills/aidd-rlm/runtime/*.py`.
- Shell wrappers are allowed only for hooks/platform glue; stage orchestration must not depend on `skills/*/scripts/*`.
- `tools/` should contain import stubs or repo-only tooling.
- Wrapper output budget: stdout ≤ 200 lines or ≤ 50 KB, stderr ≤ 50 lines; emit larger payloads into `aidd/reports/**`.
- `AIDD_SKIP_STAGE_WRAPPERS=1` exists for diagnostics only; under `strict` mode and during `review|qa` stages it triggers a blocking `reason_code=wrappers_skipped_unsafe`.

## Evidence read policy (summary)
- Primary evidence (research): `aidd/reports/research/<ticket>-rlm.pack.json`.
- Request slices on demand: `python3 ${AIDD_ROOT}/skills/aidd-rlm/runtime/rlm_slice.py --ticket <ticket> --query "<token>"`.

## Migration policy (legacy -> RLM-only)
- Legacy pre-RLM research context/targets artifacts are not read by gates and do not count as evidence.
- For older workspaces rebuild the research stage: `python3 ${AIDD_ROOT}/skills/researcher/runtime/research.py --ticket <ticket> --auto`.
- If research leaves `rlm_status=pending`, hand off to the shared owner: `python3 ${AIDD_ROOT}/skills/aidd-rlm/runtime/rlm_finalize.py --ticket <ticket>`.
- Plan/review/qa gates require the minimum RLM set: `rlm-targets`, `rlm-manifest`, `rlm.worklist.pack`, `rlm.nodes`, `rlm.links`, `rlm.pack`.

## Capturing user answers
Respond within the same command/stage. If answers are delivered via chat, ask the user to paste:
```
## AIDD:ANSWERS
- Answer 1: ...
- Answer 2: ...
```
