# AIDD Plugin Modernization Plan

Purpose: close the known gaps between this multi-IDE port and the upstream `ai_driven_dev` project so future tasklists can reference concrete milestones.

## Phase 0 – Baseline Assessment (Week 0)
- [x] Validate current workspace bootstrap by running `python3 skills/aidd-init/runtime/init.py --force` inside a temp folder; capture failures as blockers.
- [x] Inventory missing assets vs. upstream (`docs/overview.md`, `aidd-plugin与AIDD核心差距分析报告.md`) and confirm required directories (agents/, templates/, hooks/).
- [x] Freeze dependency versions in `pyproject.toml` and document environment expectations in `README.md` + `AGENTS.md`.

## Phase 1 – Core Assets & Templates (Week 1)
- [x] Port workspace templates from `ai_driven_dev/templates/aidd` plus stage-specific templates (PRD/plan/tasklist/spec/context) to `templates/aidd/`.
- [x] Ensure `skills/aidd-init/runtime/init.py:19-44` references valid template paths (rename seeds if needed) and add a pytest that runs init inside `tmp_path` and asserts expected files exist.
- [x] Restore shared skill templates such as `skills/aidd-core/templates/workspace-agents.md` to keep docs in sync with init output.

## Phase 2 – Agents Library (Week 2)
- [x] Create `agents/` directory and port the 11 canonical agent specs (analyst, researcher, planner, validator, prd-reviewer, plan-reviewer, spec-interview-writer, tasklist-refiner, implementer, reviewer, qa).
- [x] Normalize environment variables (legacy plugin-root var → `AIDD_ROOT`), language mix, and tool permissions inside each agent file so they align with multi-IDE targets.
- [x] Add schema validation (pytest) ensuring every agent file contains required sections (`---`, `<role>`, `<process>`, `<output>`).

## Priority Phase – Bootstrap & Layout Convergence (Now)
Execution rule: finish this phase before Phase 3+ to avoid duplicated path churn.
- [x] Unify runtime/hook entrypoint bootstrap so scripts rely on `AIDD_ROOT` and self-inject `sys.path` (`<repo>`), with no manual `PYTHONPATH` requirement.
- [x] Produce a minimal layout-convergence migration checklist (target single canonical layout, move map, import rewrites, command/docs rewrites, rollback points). Deliverable: `docs/layout-convergence-min-migration.md`.
- [x] Execute the layout convergence migration and remove temporary bridges/fallbacks in one pass. Result: migrated to `aidd_runtime/` + `skills/*/runtime/`, rewrote skills/hooks/docs/tests path references, and removed `PYTHONPATH` fallback injections from runtime/hook code paths.
- [x] Add migration smoke tests (init/research/qa/hooks) and record outcomes in `README.md` and `COMMANDS.md`. Added `tests/runtime/test_layout_migration_smoke.py`; verified with `pytest -q tests/runtime/test_layout_migration_smoke.py tests/runtime/test_init_runtime.py tests/test_runtime_basic.py` (12 passed).

## Phase 3 – Stage & Shared Skills (Weeks 3-4)
- [x] Replace the simplified `/flow:aidd-*-flow` SKILL docs with the upstream stage commands (`skills/idea-new/SKILL.md`, `plan-new`, `tasks-new`, `implement`, `review`, `qa`, `researcher`, `review-spec`, `spec-interview`). Result: stage command skills are now primary; legacy flow skills remain as compatibility shims.
- [x] Reintroduce shared skills (`aidd-policy`, `aidd-reference`, `aidd-stage-research`) so subagents inherit consistent policy, read discipline, and loop safety guidance.
- [x] Update `scripts/install.sh` and docs so new skills are symlinked and discoverable via `/skill:` commands in Kimi/Cursor/Codex. Result: installer links only dirs containing `SKILL.md`, and `scripts/verify-flows.sh` validates required stage skills.

## Phase 4 – Stage Dispatch Runtime & IDE Profiles (Weeks 4-6)
Note: after Phase 3, stage-command skills (`/skill:*`) are the primary interface, so this phase targets dispatch/profile convergence instead of a standalone Mermaid flow parser.
- [x] Implement `aidd_runtime/stage_dispatch.py` to map stage commands to runtime entrypoints, normalize legacy flow aliases, and drive state transitions through `aidd-flow-state`. Result: baseline dispatch + command execution layer and tests are added (`aidd_runtime/stage_dispatch.py`, `aidd_runtime/command_runner.py`, `tests/runtime/test_stage_dispatch.py`, `tests/runtime/test_command_runner.py`); P4.1 subtask checklist in `docs/p4.1-stage-dispatch-checklist.md` is fully completed.
- [x] Add `aidd_runtime/ide_profiles.py` and wire it into `aidd_runtime/command_runner.py` to absorb host-protocol differences (for example command prefix dialect, skills discovery path, timeout/output limits, permission toggles), while keeping stage/runtime business logic single-path.
  Result: `ide_profiles.select_profile()` now centralizes selection order (explicit profile -> command prefix -> env hints -> single skills-dir detection -> default), `command_runner.build_runtime_env()` now exports discovered `AIDD_SKILLS_DIRS/AIDD_PRIMARY_SKILLS_DIR`, and the strategy is documented in `docs/p4.2-ide-profiles.md`.
- [ ] Add orchestration integration tests for `idea-new -> researcher -> plan-new -> tasks-new` plus legacy flow alias compatibility, validating `.active.json` and generated artifacts.

## Phase 5 – Automation Hooks & Gates (Week 7)
- [x] Port hook scripts from upstream (`hooks/format-and-test.sh`, `gate-tests.sh`, `gate-qa.sh`, `gate-workflow.sh`, `context-gc-*.sh`) with updated env vars.
- [ ] Wire hooks into `skills/aidd-core/runtime/gates.py` so stage commands can enforce readiness gates (analyst_check, research_check, plan_review_gate, diff_boundary_check, qa_gate).
- [ ] Document hook usage in `COMMANDS.md` and add CI-friendly wrappers for Codex CLI users.

## Phase 6 – Testing & QA Expansion (Weeks 8-9)
- [ ] Backfill critical pytest suites from `ai_driven_dev/tests` (active_state, gates, docio, loop, hooks) and adapt fixtures for the new stage-dispatch / IDE-profile runtime.
- [ ] Tighten `scripts/test.sh` to fail on Black/Ruff/MyPy issues and capture coverage for `aidd_runtime/stage_dispatch.py`, `aidd_runtime/command_runner.py`, and `aidd_runtime/ide_profiles.py`.
- [ ] Add end-to-end tests that initialize a workspace, run the idea → research → plan pipeline, and assert generated artifacts (PRD, research pack, plan, tasklist).

## Phase 7 – Documentation & Adoption (Week 10+)
- [ ] Update `README.md`, `QUICKSTART.md`, and `docs/overview.md` with stage-dispatch runtime instructions, IDE profile configuration, and hook usage.
- [ ] Link the new plan (this file) from `AGENTS.md` and future tasklists so contributors can track progress.
- [ ] Publish a migration checklist comparing upstream commands vs. Codex CLI equivalents for teams moving from Claude Code.

Deliverables from each phase become input to structured tasklists (e.g., per phase -> tasks {T1, T2, ...}) used by loop implementers. Adjust timeline based on staffing; phases should not overlap unless dependencies are satisfied.
