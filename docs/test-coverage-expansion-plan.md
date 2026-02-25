# Test Coverage Expansion Plan

> Date: 2026-02-20  
> Scope: `aidd-plugin` test coverage uplift against current gap with upstream `ai_driven_dev`.

## 1. Baseline

- Current repo test files: `16` (`tests/runtime`: `13`)
- Current repo test LOC: `1284`
- Upstream repo test files: `89`
- Historical baseline `./scripts/test.sh` total coverage: `47%` (pre-WP coverage scope)

Coverage metric scope (current):

- `Total coverage` in this plan refers to the aggregate percentage reported by `./scripts/test.sh`.
- `./scripts/test.sh` uses `.coveragerc` to report a scoped aggregate for:
  - `aidd_runtime/*.py`
  - key hooks (`hooklib`, `gate-*`, `format-and-test`, `gate-workflow`)
  - WP-2~WP-5 targeted skill runtimes (`gate_workflow`, flow-state tasklist/progress/stage_result, RLM stack)
- It intentionally excludes unrelated skill runtimes (for example `context_gc` hook modules and non-target stage agents)
  so the KPI reflects the modules covered by this plan.
- Current scoped aggregate after WP-1..WP-5: `74%` (measured via `./scripts/test.sh` on 2026-02-25).

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

- Raise total coverage (per `./scripts/test.sh` + `.coveragerc` scoped aggregate) from `47%` to `>=60%`.
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

- [x] Add `tests/runtime/test_gate_workflow_unit.py` (parser, scope, gate ordering)
- [x] Add `tests/runtime/test_gate_workflow_preflight_contract.py`
- [x] Add `tests/hooks/test_gate_tests_hook.py`
- [x] Add `tests/hooks/test_gate_qa_hook.py`
- [x] Add `tests/hooks/test_format_and_test_hook.py`

Acceptance:

- `skills/aidd-core/runtime/gate_workflow.py >= 45%` (covered by WP-2新增单测)
- `hooks/*` key entry scripts covered by smoke + behavior tests (completed)

## WP-3 (Flow-State / Tasklist)

- [x] Add `tests/flow_state/test_tasklist_parser.py` (覆盖 `tasklist_check` parser helpers)
- [x] Add `tests/flow_state/test_tasklist_normalize.py`
- [x] Add `tests/flow_state/test_tasklist_validate.py`
- [x] Add `tests/flow_state/test_progress.py`
- [x] Add `tests/flow_state/test_stage_result.py`

Acceptance:

- `tasklist_normalize.py >= 35%` (current: `83%`)
- `progress.py >= 45%` (current: `57%`)
- `stage_result.py >= 65%` (current: `70%`)

## WP-4 (RLM Stack)

- [x] Add `tests/rlm/test_rlm_targets.py`
- [x] Add `tests/rlm/test_rlm_nodes_build.py`
- [x] Add `tests/rlm/test_reports_pack.py`
- [x] Add `tests/rlm/test_reports_pack_assemble.py`
- [x] Add `tests/rlm/test_rlm_verify.py`

Acceptance:

- `reports_pack.py >= 45%` (current: `73%`)
- `rlm_nodes_build.py >= 50%` (current: `78%`)
- `reports_pack_assemble.py >= 35%` (current: `89%`)

## WP-5 (Stage E2E + Regression)

- [x] Add failure-path e2e: missing hints / blocked gates / missing ticket
- [x] Add hooks + stage orchestration combined smoke
- [x] Add regression tests for legacy flow alias mapping and profile auto-detection

Acceptance:

- Stage chain (`idea -> research -> plan -> tasks -> implement/review/qa`) has positive + negative-path coverage. (WP-5 regression/negative-path tests added)

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

- [x] Total coverage `>= 60%` (measured by `./scripts/test.sh` with current `.coveragerc` scope)
- [ ] Test file count `>= 40`
- [ ] All WP acceptance conditions met
- [ ] No new flaky tests in 3 consecutive CI runs
