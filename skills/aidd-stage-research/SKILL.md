---
name: aidd-stage-research
description: Stage-specific research contract for evidence reading and handoff behavior.
lang: en
model: inherit
user-invocable: false
---

## Scope
- Preload-only reference for subagent `researcher`.
- Defines RLM-only evidence and handoff behavior.

## Stage Contract
- `skills/researcher/SKILL.md` owns orchestration.
- `agents/researcher.md` owns research content updates.
- Subagent must not run shared RLM owner internals directly.

## Evidence policy
- Read pack first: `aidd/reports/research/<ticket>-rlm.pack.json`.
- If pack is missing, use `*-rlm.worklist.pack.json` and return BLOCKED with handoff.
- Use targeted slice queries before broad reads.

## Handoff policy
- If `rlm_status` is not ready, return BLOCKED with:
  `python3 ${AIDD_ROOT}/skills/aidd-rlm/runtime/rlm_finalize.py --ticket <ticket>`.
- If ready, update research doc and return READY with next-stage hint.
