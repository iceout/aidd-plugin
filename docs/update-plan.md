# AIDD Plugin Modernization Plan

Purpose: close the known gaps between this multi-IDE port and the upstream `ai_driven_dev` project so future tasklists can reference concrete milestones.

## Phase 0 – Baseline Assessment (Week 0)
- [ ] Validate current workspace bootstrap by running `python3 runtime/skills/aidd-init/runtime/init.py --force` inside a temp folder; capture failures as blockers.
- [ ] Inventory missing assets vs. upstream (`docs/overview.md`, `aidd-plugin与AIDD核心差距分析报告.md`) and confirm required directories (agents/, templates/, hooks/).
- [ ] Freeze dependency versions in `pyproject.toml` and document environment expectations in `README.md` + `AGENTS.md`.

## Phase 1 – Core Assets & Templates (Week 1)
- [ ] Port workspace templates from `ai_driven_dev/templates/aidd` plus stage-specific templates (PRD/plan/tasklist/spec/context) to `templates/aidd/`.
- [ ] Ensure `runtime/skills/aidd-init/runtime/init.py:19-44` references valid template paths (rename seeds if needed) and add a pytest that runs init inside `tmp_path` and asserts expected files exist.
- [ ] Restore shared skill templates such as `skills/aidd-core/templates/workspace-agents.md` to keep docs in sync with init output.

## Phase 2 – Agents Library (Week 2)
- [ ] Create `agents/` directory and port the 11 canonical agent specs (analyst, researcher, planner, validator, prd-reviewer, plan-reviewer, spec-interview-writer, tasklist-refiner, implementer, reviewer, qa).
- [ ] Normalize environment variables (legacy plugin-root var → `AIDD_ROOT`), language mix, and tool permissions inside each agent file so they align with multi-IDE targets.
- [ ] Add schema validation (pytest) ensuring every agent file contains required sections (`---`, `<role>`, `<process>`, `<output>`).

## Phase 3 – Stage & Shared Skills (Weeks 3-4)
- [ ] Replace the simplified `/flow:aidd-*-flow` SKILL docs with the upstream stage commands (`skills/idea-new/SKILL.md`, `plan-new`, `tasks-new`, `implement`, `review`, `qa`, `researcher`, `review-spec`, `spec-interview`).
- [ ] Reintroduce shared skills (`aidd-policy`, `aidd-reference`, `aidd-stage-research`) so subagents inherit consistent policy, read discipline, and loop safety guidance.
- [ ] Update `scripts/install.sh` and docs so new skills are symlinked and discoverable via `/skill:` commands in Kimi/Cursor/Codex.

## Phase 4 – Flow Runtime & IDE Adapter (Weeks 4-6)
- [ ] Implement `runtime/flow_engine.py` that can execute flow definitions: resolve inputs, call stage runtimes, and transition states using `aidd-flow-state` utilities.
- [ ] Add `runtime/agent_caller.py` plus `runtime/ide_adapter.py` with `KimiAdapter`, `CursorAdapter`, and `CodexAdapter` to abstract tool invocation differences.
- [ ] Extend each flow SKILL with `runtime:` metadata pointing to the new engine entrypoints and add integration tests that drive a toy ticket through idea → implement.

## Phase 5 – Automation Hooks & Gates (Week 7)
- [ ] Port hook scripts from upstream (`hooks/format-and-test.sh`, `gate-tests.sh`, `gate-qa.sh`, `gate-workflow.sh`, `context-gc-*.sh`) with updated env vars.
- [ ] Wire hooks into `runtime/skills/aidd-core/runtime/gates.py` so flows can enforce readiness gates (analyst_check, research_check, plan_review_gate, diff_boundary_check, qa_gate).
- [ ] Document hook usage in `COMMANDS.md` and add CI-friendly wrappers for Codex CLI users.

## Phase 6 – Testing & QA Expansion (Weeks 8-9)
- [ ] Backfill critical pytest suites from `ai_driven_dev/tests` (active_state, gates, docio, loop, hooks) and adapt fixtures for the new adapters.
- [ ] Tighten `scripts/test.sh` to fail on Black/Ruff/MyPy issues and capture coverage for `runtime/flow_engine.py` + adapters.
- [ ] Add end-to-end tests that initialize a workspace, run the idea → research → plan pipeline, and assert generated artifacts (PRD, research pack, plan, tasklist).

## Phase 7 – Documentation & Adoption (Week 10+)
- [ ] Update `README.md`, `QUICKSTART.md`, and `docs/overview.md` with flow-runtime instructions, IDE adapter configuration, and hook usage.
- [ ] Link the new plan (this file) from `AGENTS.md` and future tasklists so contributors can track progress.
- [ ] Publish a migration checklist comparing upstream commands vs. Codex CLI equivalents for teams moving from Claude Code.

Deliverables from each phase become input to structured tasklists (e.g., per phase -> tasks {T1, T2, ...}) used by loop implementers. Adjust timeline based on staffing; phases should not overlap unless dependencies are satisfied.
