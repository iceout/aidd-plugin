---
name: aidd-research-flow
description: Legacy flow compatibility entry. Use stage command skills instead.
type: flow
---

# Legacy Flow Compatibility

This flow entry is retained for compatibility during migration.

## Recommended replacement
- `aidd-idea-flow` -> `/skill:idea-new <ticket> [note...]`
- `aidd-research-flow` -> `/skill:researcher <ticket> [--paths ... --keywords ...]`
- `aidd-plan-flow` -> `/skill:plan-new <ticket> [note...]`
- `aidd-implement-flow` -> `/skill:implement <ticket> [note...]`
- `aidd-review-flow` -> `/skill:review <ticket> [note...]`
- `aidd-qa-flow` -> `/skill:qa <ticket> [note...]`

## Notes
- Stage orchestration is now owned by stage command skills.
- New shared policy skills: `aidd-policy`, `aidd-reference`, `aidd-stage-research`.
