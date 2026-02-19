---
name: aidd-policy
description: Shared policy contract for output format, read discipline, question format, and loop safety.
lang: en
model: inherit
user-invocable: false
---

## Scope
- Single source of truth for reusable policy guidance.
- Stage/runtime ownership stays in `aidd-core` and stage skills.
- Intended for subagent preload.

## Output contract (required)
- Status: ...
- Work item key: ...
- Artifacts updated: ...
- Tests: ...
- Blockers/Handoff: ...
- Next actions: ...
- AIDD:READ_LOG: ...
- AIDD:ACTIONS_LOG: ...

## Question format
Use this exact format:

```text
Question N (Blocker|Clarification): ...
Why: ...
Options: A) ... B) ...
Default: ...
```

## Read policy (pack-first)
- Read packs/slices before full files.
- Prefer `rlm_slice.py` and section slices.
- Keep `AIDD:READ_LOG` compact and artifact-linked.

## Loop safety
- `AIDD_SKIP_STAGE_WRAPPERS=1` is diagnostics-only.
- In strict mode or `review|qa`, bypass is blocked (`wrappers_skipped_unsafe`).
- In fast mode on `implement`, bypass may warn (`wrappers_skipped_warn`) for diagnostics only.

## Additional resources
- [references/output-contract.md](references/output-contract.md)
- [references/read-policy.md](references/read-policy.md)
- [references/question-format.md](references/question-format.md)
- [references/loop-safety.md](references/loop-safety.md)
