# Research Summary — {{feature}}

Status: pending
Last reviewed: {{date}}
Commands:
  Research scan: python3 ${AIDD_ROOT}/skills/researcher/runtime/research.py --ticket {{ticket}} --auto --paths {{paths}} --keywords {{keywords}}
  Search: rg "{{ticket|feature}}" {{modules}}
Artifacts:
  PRD: aidd/docs/prd/{{ticket}}.prd.md
  Tasklist: aidd/docs/tasklist/{{ticket}}.md

## AIDD:CONTEXT_PACK
- {{summary_short}}
- Limit: ≤ 20 lines / ≤ 1200 chars.
- Paths discovered: {{paths_discovered}}
- Invalid paths: {{invalid_paths}}
- Pack-first: rely on `*-rlm.pack.*` and `rlm_slice`; do not dump raw JSONL.

## AIDD:PRD_OVERRIDES
{{prd_overrides}}
- Must match the PRD (`USER OVERRIDE`) and stay consistent with accepted decisions.

## AIDD:NON_NEGOTIABLES
- {{non_negotiables}}

## AIDD:OPEN_QUESTIONS
- {{open_questions}}

## AIDD:RISKS
- {{risks}}

## AIDD:DECISIONS
- {{decisions}}

## AIDD:INTEGRATION_POINTS
- {{integration_points}}

## AIDD:REUSE_CANDIDATES
- {{reuse_candidates}}

## AIDD:COMMANDS_RUN
- {{commands_run}}

## AIDD:RLM_EVIDENCE
- Status: {{rlm_status}}
- Pack: {{rlm_pack_path}}
- Pack status: {{rlm_pack_status}}
- Pack bytes: {{rlm_pack_bytes}}
- Pack updated_at: {{rlm_pack_updated_at}}
- Warnings: {{rlm_warnings}} (e.g., rlm_links_empty_warn)
- Slice: python3 ${AIDD_ROOT}/skills/aidd-rlm/runtime/rlm_slice.py --ticket {{ticket}} --query "<token>"
- Nodes/links: {{rlm_nodes_path}} / {{rlm_links_path}} (do not read in full)

## AIDD:TEST_HOOKS
- {{test_hooks}}
- Evidence: {{tests_evidence}}
- Suggested tasks: {{suggested_test_tasks}}

## Context Pack (TL;DR)
- **Entry points:** {{entry_points}}
- **Reuse candidates:** {{reuse_candidates}}
- **Integration points:** {{integration_points}}
- **RLM:** {{rlm_summary}} (pack: {{rlm_pack_path}})
- **Test pointers:** {{test_pointers}}
- **Top risks:** {{risks}}
- Keep it concise; may be longer than AIDD:CONTEXT_PACK if needed.

## Definition of reviewed
- At least one integration point found or the baseline is explicitly documented.
- Tests/contracts are referenced, or the risk “no tests” is explicitly recorded.
- Commands/scan paths and report links are captured.

## Context
- **Feature goal:** {{goal}}
- **Scope of change:** {{scope}}
- **Key modules/directories:** {{modules}}
- **Source artifacts:** {{inputs}}
- **Command logs / reports:** {{logs}}

## Integration points
- {{target-point}} (file/class/endpoint → where we hook in → related calls/imports)

## Reuse opportunities
- {{reused-component}} (path → how to reuse → risks → tests/contracts)

## Established practices
- {{guideline}} (link to the test/log/contract proving it)

## RLM evidence (if applicable)
- {{rlm-note}} (summary of modules/links; use rlm_slice for precise lookups)
- Pack: {{rlm_pack_path}}

## Patterns / anti-patterns
- **Patterns:** {{positive-patterns}} (link to code/tests)
- **Anti-patterns:** {{negative-patterns}} (link to code/tests)

## Missing patterns / missing data
- {{empty-context-note}} (list commands/paths that yielded no context)

## Gap analysis
- {{gap-description}} (reference the limitation + proposed mitigation)

## Next steps
- {{next-step}} (state who updates which file/command)

## Additional notes
- {{manual-note}}

## Open questions
- {{question}}
