---
name: researcher
description: Run research pipeline and produce RLM-backed research artifacts.
argument-hint: $1 [note...] [--paths path1,path2] [--keywords kw1,kw2] [--note text]
lang: en
model: inherit
disable-model-invocation: true
user-invocable: true
---

Follow `aidd-core`.

## Steps
1. Set active feature and stage `research`.
2. Run canonical pipeline: `python3 ${AIDD_ROOT}/skills/researcher/runtime/research.py --ticket <ticket> --auto`.
3. Re-run with optional overrides (`--paths`, `--keywords`, `--note`) when targeted refresh is required.
4. Validate RLM outputs (`*-rlm-targets.json`, `*-rlm-manifest.json`, `*-rlm.worklist.pack.json`, `*-rlm.pack.json`).
5. Run subagent `researcher`, reading pack/worklist first.
6. If RLM is still pending, return BLOCKED with handoff:
   `python3 ${AIDD_ROOT}/skills/aidd-rlm/runtime/rlm_finalize.py --ticket <ticket>`.
7. Return output contract and next step `/skill:plan-new <ticket>` when ready.

## Command contracts
### `python3 ${AIDD_ROOT}/skills/researcher/runtime/research.py`
- When: always as the research-stage entrypoint.
- Inputs: `--ticket <ticket>` with optional path/keyword/note overrides.
- Outputs: research artifacts and RLM readiness markers.
- Failure mode: exits non-zero when required inputs/artifacts are missing.
- Next action: fix inputs and rerun.

## Additional resources
- [templates/research.template.md](../../templates/aidd/docs/research/template.md)
- [../aidd-rlm/SKILL.md](../aidd-rlm/SKILL.md)
