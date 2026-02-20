# Test Coverage Expansion Plan

> Date: 2026-02-20  
> Scope: `aidd-plugin` test coverage uplift against current gap with upstream `ai_driven_dev`.

## 1. Baseline

- Current repo test files: `16` (`tests/runtime`: `13`)
- Current repo test LOC: `1284`
- Upstream repo test files: `89`
- Current `./scripts/test.sh` total coverage: `47%`

High-risk low-coverage modules (selected):

- `aidd_runtime/readiness_gates.py` (`28%`)
- `aidd_runtime/runtime.py` (`56%`)
- `aidd_runtime/io_utils.py` (`40%`)
- `skills/aidd-core/runtime/gate_workflow.py` (`15%`)
- `skills/aidd-core/runtime/research_guard.py` (`42%`)
- `skills/aidd-core/runtime/qa_agent.py` (`61%`)
- `skills/aidd-flow-state/runtime/tasklist_normalize.py` (`8%`)
- `skills/aidd-flow-state/runtime/progress.py` (`21%`)
- `skills/aidd-rlm/runtime/reports_pack.py` (`30%`)
- `skills/aidd-rlm/runtime/rlm_nodes_build.py` (`31%`)

## 2. Target

- Raise total coverage from `47%` to `>=60%`.
- Expand test files from `16` to `>=40`.
- Ensure all core gate and stage-dispatch paths have negative-path tests.
- Preserve strict gate: `./scripts/test.sh` stays green at each batch.

## 3. Work Packages

## WP-1 (Core Runtime)

- [x] Add `tests/runtime/test_io_utils.py`
- [x] Add `tests/runtime/test_runtime_paths_and_settings.py`
- [x] Add `tests/runtime/test_readiness_gates_full.py` (success/failure/skip branches)
- [x] Extend stage-dispatch coverage with gate-on/off and ticket injection edge cases (`tests/runtime/test_stage_dispatch_edges.py`)

Acceptance:

- `aidd_runtime/io_utils.py >= 80%` (current: `97%`)
- `aidd_runtime/runtime.py >= 70%` (current: `84%`)
- `aidd_runtime/readiness_gates.py >= 65%` (current: `80%`)

## WP-2 (Gate Workflow + Hooks)

- [ ] Add `tests/runtime/test_gate_workflow_unit.py` (parser, scope, gate ordering)
- [ ] Add `tests/runtime/test_gate_workflow_preflight_contract.py`
- [ ] Add `tests/hooks/test_gate_tests_hook.py`
- [ ] Add `tests/hooks/test_gate_qa_hook.py`
- [ ] Add `tests/hooks/test_format_and_test_hook.py`

Acceptance:

- `skills/aidd-core/runtime/gate_workflow.py >= 45%`
- `hooks/*` key entry scripts covered by smoke + behavior tests

## WP-3 (Flow-State / Tasklist)

- [ ] Add `tests/flow_state/test_tasklist_parser.py`
- [ ] Add `tests/flow_state/test_tasklist_normalize.py`
- [ ] Add `tests/flow_state/test_tasklist_validate.py`
- [ ] Add `tests/flow_state/test_progress.py`
- [ ] Add `tests/flow_state/test_stage_result.py`

Acceptance:

- `tasklist_normalize.py >= 35%`
- `progress.py >= 45%`
- `stage_result.py >= 65%`

## WP-4 (RLM Stack)

- [ ] Add `tests/rlm/test_rlm_targets.py`
- [ ] Add `tests/rlm/test_rlm_nodes_build.py`
- [ ] Add `tests/rlm/test_reports_pack.py`
- [ ] Add `tests/rlm/test_reports_pack_assemble.py`
- [ ] Add `tests/rlm/test_rlm_verify.py`

Acceptance:

- `reports_pack.py >= 45%`
- `rlm_nodes_build.py >= 50%`
- `reports_pack_assemble.py >= 35%`

## WP-5 (Stage E2E + Regression)

- [ ] Add failure-path e2e: missing hints / blocked gates / missing ticket
- [ ] Add hooks + stage orchestration combined smoke
- [ ] Add regression tests for legacy flow alias mapping and profile auto-detection

Acceptance:

- Stage chain (`idea -> research -> plan -> tasks -> implement/review/qa`) has positive + negative-path coverage.

## 4. Upstream Mapping Backlog

Prioritized upstream tests to port/adapt first:

- `test_gate_workflow.py`
- `test_gate_workflow_preflight_contract.py`
- `test_format_and_test.py`
- `test_gate_tests_hook.py`
- `test_gate_qa.py`
- `test_tasklist_normalize.py`
- `test_progress.py`
- `test_stage_result.py`
- `test_rlm_targets.py`
- `test_reports_pack.py`
- `test_rlm_nodes_build.py`
- `test_qa_agent.py`
- `test_research_hints.py`
- `test_review_pack.py`

## 5. Execution Order

1. WP-1 (lowest risk, fastest uplift).
2. WP-2 (gate/hook contract safety).
3. WP-3 (flow-state debt).
4. WP-4 (RLM heavy modules).
5. WP-5 (system regression hardening).

Each WP must be merged only after:

- `./scripts/test.sh` passes.
- Coverage delta is recorded in PR description.
- New tests are deterministic (no network / no non-local side effects).

## 6. Done Criteria

This plan is done when all below are true:

- [ ] Total coverage `>= 60%`
- [ ] Test file count `>= 40`
- [ ] All WP acceptance conditions met
- [ ] No new flaky tests in 3 consecutive CI runs
