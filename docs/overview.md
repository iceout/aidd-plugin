# AIDD Plugin Overview

## 1. 项目目标

AIDD Plugin 为 Kimi/Cursor/Codex 提供统一的 AI-Driven Development 工作流：

- Idea -> Research -> Plan -> Tasklist -> Implement -> Review -> QA
- 同一套阶段逻辑，不按 IDE 分叉业务实现
- 通过 stage dispatch、IDE profiles、readiness gates 统一调度

## 2. 当前架构

```text
AI IDE command
   │
   ▼
SKILL.md (skills/*)
   │
   ▼
aidd_runtime/stage_dispatch.py
   ├── ide_profiles.py         # 宿主命令方言/skills 目录/环境差异
   ├── command_runner.py       # 统一执行、超时与输出限制
   ├── readiness_gates.py      # implement/review/qa 预检 gate
   └── runtime.py              # 路径、active state、工件辅助
   │
   ▼
skills/*/runtime/*.py          # 各阶段入口脚本
   │
   ▼
workspace/aidd/*               # docs/reports/config/.cache
```

运行时代码布局已收敛为：

- `aidd_runtime/`（共享 runtime）
- `skills/*/runtime/`（阶段与共享脚本）

旧布局 `runtime/aidd_runtime` 与 `runtime/skills` 已移除。

## 3. Stage Dispatch 模型

核心映射在 `aidd_runtime/stage_dispatch.py`：

- `aidd-init-flow` -> `skills/aidd-init/runtime/init.py`
- `idea-new` -> `skills/idea-new/runtime/analyst_check.py`
- `researcher` -> `skills/researcher/runtime/research.py`
- `plan-new` -> `skills/plan-new/runtime/research_check.py`
- `review-spec` -> `skills/review-spec/runtime/prd_review_cli.py`
- `spec-interview` -> `skills/spec-interview/runtime/spec_interview.py`
- `tasks-new` -> `skills/tasks-new/runtime/tasks_new.py`
- `implement` -> `skills/implement/runtime/implement_run.py`
- `review` -> `skills/review/runtime/review_run.py`
- `qa` -> `skills/aidd-core/runtime/qa_gate.py`

同时支持 legacy flow alias 归一：

- `aidd-idea-flow` -> `idea-new`
- `aidd-research-flow` -> `researcher`
- `aidd-plan-flow` -> `plan-new`
- `aidd-implement-flow` -> `implement`
- `aidd-review-flow` -> `review`
- `aidd-qa-flow` -> `qa`

调度默认行为：

- 自动读取/注入 `--ticket`
- 自动写入 active feature/stage
- `implement/review/qa` 默认先跑 preflight gates
- 可用 `AIDD_STAGE_DISPATCH_GATES=0` 关闭 preflight

## 4. IDE Profiles

Profile 定义在 `aidd_runtime/ide_profiles.py`，内置：`kimi`、`codex`、`cursor`。

默认选择顺序：

1. 显式 profile 参数
2. 命令前缀识别（如 `$aidd:...`）
3. `AIDD_IDE_PROFILE` / `AIDD_HOST`
4. skills 目录自动探测
5. 默认 `kimi`

默认 skills 目录：

- kimi: `~/.config/agents/skills`
- codex: `~/.codex/skills`
- cursor: `~/.cursor/skills`

可覆盖：

- `AIDD_SKILLS_DIRS`（多目录，`os.pathsep` 分隔）

## 5. Hooks 与 Gates

Hooks 入口位于 `hooks/`，统一要求设置 `AIDD_ROOT`。

常用入口：

- `hooks/gate-workflow.sh`
- `hooks/gate-tests.sh`
- `hooks/gate-qa.sh`
- `hooks/format-and-test.sh`

建议在目标项目工作区执行，不要在插件仓库根目录执行业务 gate。

## 6. 推荐命令

阶段主命令：

- `/flow:aidd-init-flow`
- `/skill:idea-new <ticket>`
- `/skill:researcher <ticket>`
- `/skill:plan-new <ticket>`
- `/skill:tasks-new <ticket>`
- `/skill:implement <ticket>`
- `/skill:review <ticket>`
- `/skill:qa <ticket>`

详细命令见 `COMMANDS.md`。

## 7. 相关文档

- `README.md`
- `QUICKSTART.md`
- `docs/p4.2-ide-profiles.md`
- `docs/layout-convergence-min-migration.md`
- `docs/update-plan.md`
