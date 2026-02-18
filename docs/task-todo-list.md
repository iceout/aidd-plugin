# AIDD Plugin Modernization TODOs

> 说明：本计划引用的 upstream 仓库 `ai_driven_dev` 对应本地路径 `/Users/xuanyizhang/code/ai_driven_dev`，后续同步/对比均以该路径为准。

## Phase 0 – Baseline Assessment (Week 0)
- [x] **T0.1** 运行 `python3 runtime/skills/aidd-init/runtime/init.py --force` 于隔离 temp 目录，保存执行日志并把任何失败登记为 blocker。
- [x] **T0.2** 对比 `/Users/xuanyizhang/code/ai_driven_dev` 缺失资产（`docs/overview.md`, `aidd-plugin与AIDD核心差距分析报告.md` 等），补齐 `agents/`, `templates/`, `hooks/` 目录并输出差距清单。
- [x] **T0.3** 在 `pyproject.toml` 冻结依赖版本，并把环境要求同步写入 `README.md` 与 `AGENTS.md`。

## Phase 1 – Core Assets & Templates (Week 1)
- [x] **T1.1** 迁移 `ai_driven_dev/templates/aidd` 与 PRD/plan/tasklist/spec/context 模板至 `templates/aidd/`。
- [x] **T1.2** 校正 `runtime/skills/aidd-init/runtime/init.py:19-44` 的模板路径，新增基于 `tmp_path` 的 pytest，确保 init 后的文件集正确。
- [x] **T1.3** 恢复共享模板 `skills/aidd-core/templates/workspace-agents.md`，保证 init 输出与文档一致。

## Phase 2 – Agents Library (Week 2)
- [x] **T2.1** 创建 `agents/` 并移植 11 个标准 Agent 规格（analyst, researcher, planner, validator, prd-reviewer, plan-reviewer, spec-interview-writer, tasklist-refiner, implementer, reviewer, qa）。
- [x] **T2.2** 统一 Agent 文件中的环境变量（legacy 插件根变量 → `AIDD_ROOT`）、语言描述与工具权限，适配多 IDE。
- [x] **T2.3** 编写 schema 验证 pytest，检查每个 Agent 是否包含 `---`, `<role>`, `<process>`, `<output>` 分段。

## Priority Phase – Bootstrap & Layout Convergence (Now)
> 说明：该阶段优先级高于 Phase 3+，用于先解决运行入口和目录结构分裂问题，避免后续任务重复返工。
- [x] **P1.1** 统一所有 runtime/hook 入口的自举约定：仅使用 `AIDD_ROOT`，入口脚本负责注入 `sys.path`（`<repo>/runtime` + `<repo>`），禁止依赖手工设置 `PYTHONPATH`。  
  完成情况：已为 `runtime/` 与 `hooks/` 下全部 `__main__` 入口注入统一 `_bootstrap_entrypoint()`，并验证 `research/rlm_targets/qa` 入口在未设置 `PYTHONPATH` 时可正常启动到业务校验阶段。
- [ ] **P1.2** 产出“目录收敛最小迁移清单”：明确目标单一布局（推荐向 upstream 靠拢），列出移动路径、导入调整、命令文本更新范围和回滚点。
- [ ] **P1.3** 执行目录收敛迁移并一次性替换路径引用（skills/hook/docs/tests），移除临时桥接与隐式 fallback。
- [ ] **P1.4** 增加迁移 smoke tests（init/research/qa/hook），并把迁移结果与风险写回 `README.md`、`COMMANDS.md`。

## Phase 3 – Stage & Shared Skills (Weeks 3-4)
- [ ] **T3.1** 用 upstream 阶段 SKILL（`skills/idea-new/SKILL.md`, `plan-new`, `tasks-new`, `implement`, `review`, `qa`, `researcher`, `review-spec`, `spec-interview`）替换现有 `/flow:aidd-*-flow` 文档。
- [ ] **T3.2** 重新引入共享技能 `aidd-policy`, `aidd-reference`, `aidd-stage-research`，供子 Agent 继承统一策略与安全指引。
- [ ] **T3.3** 更新 `scripts/install.sh` 及文档，确保新技能被 `/skill:` 命令（Kimi/Cursor/Codex）正确发现。

## Phase 4 – Flow Runtime & IDE Adapter (Weeks 4-6)
- [ ] **T4.1** 实现 `runtime/flow_engine.py`，负责解析 flow、调度 stage runtimes，并通过 `aidd-flow-state` 管理状态转换。
- [ ] **T4.2** 新增 `runtime/agent_caller.py` 与 `runtime/ide_adapter.py`，提供 `KimiAdapter`, `CursorAdapter`, `CodexAdapter` 来抽象工具调用差异。
- [ ] **T4.3** 为各 flow SKILL 添加 `runtime:` 元数据，并编写串联 idea→implement 的集成测试。

## Phase 5 – Automation Hooks & Gates (Week 7)
- [x] **T5.1** 迁移 upstream hooks（`hooks/format-and-test.sh`, `gate-tests.sh`, `gate-qa.sh`, `gate-workflow.sh`, `context-gc-*.sh`）并更新环境变量。
- [ ] **T5.2** 将 hooks 接入 `runtime/skills/aidd-core/runtime/gates.py`，启用 analyst_check、research_check、plan_review_gate、diff_boundary_check、qa_gate。
- [ ] **T5.3** 在 `COMMANDS.md` 记录 hook 使用方式，并提供面向 Codex CLI 的 CI 包装脚本。

## Phase 6 – Testing & QA Expansion (Weeks 8-9)
- [ ] **T6.1** 回填 `/Users/xuanyizhang/code/ai_driven_dev/tests` 中关键 pytest（active_state, gates, docio, loop, hooks）并适配新的 adapter fixture。
- [ ] **T6.2** 加固 `scripts/test.sh`：Black/Ruff/MyPy 任一失败即退出，同时统计 `runtime/flow_engine.py` 与 adapters 的覆盖率。
- [ ] **T6.3** 编写端到端测试，执行 workspace init + idea→research→plan 流程并检查 PRD、research pack、plan、tasklist 产出。

## Phase 7 – Documentation & Adoption (Week 10+)
- [ ] **T7.1** 更新 `README.md`, `QUICKSTART.md`, `docs/overview.md`，覆盖 flow runtime 指南、IDE adapter 配置和 hook 用法。
- [ ] **T7.2** 在 `AGENTS.md` 及后续 tasklist 中引用 `docs/update-plan.md`，方便跟踪进度。
- [ ] **T7.3** 发布迁移清单，对比 upstream 命令与 Codex CLI 等效操作，指导从 Claude Code 迁移。
