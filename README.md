# AIDD for Kimi/Cursor/Codex

AIDD (AI-Driven Development) 多 IDE 插件，当前采用 **stage command + stage dispatch runtime** 的统一实现。

## 核心定位

- 单一运行时调度：`aidd_runtime/stage_dispatch.py`
- 单一路径工件：`./aidd/` 工作区（docs/reports/config/.cache）
- 多宿主兼容：Kimi、Codex、Cursor 共用同一套 stage 逻辑

## 环境要求

- Python `3.13.x`
- 建议使用仓库自带虚拟环境与 `uv`

固定依赖见 `pyproject.toml`（runtime + dev 均锁定版本）。

## 安装

### 1. 激活环境

```bash
source scripts/activate.sh
```

### 2. 安装 skills

```bash
# 安装到所有已存在的 skills 目录（Kimi/Codex/Cursor）
./scripts/install.sh

# 或按 IDE 精确安装
./scripts/install.sh --ide kimi --ide codex
./scripts/install.sh --ide cursor
```

### 3. 设置插件根路径

```bash
export AIDD_ROOT=/path/to/aidd-plugin
```

### 4. 验证安装

```bash
./scripts/verify-flows.sh
python3 $AIDD_ROOT/skills/aidd-observability/runtime/doctor.py
```

## 使用方式（Stage Commands）

首次在目标项目执行：

```text
/flow:aidd-init-flow
```

之后按阶段执行：

```text
/skill:idea-new <ticket> "需求描述"
/skill:researcher <ticket>
/skill:plan-new <ticket>
/skill:review-spec <ticket>
/skill:spec-interview <ticket>
/skill:tasks-new <ticket>
/skill:implement <ticket>
/skill:review <ticket>
/skill:qa <ticket>
```

兼容别名（迁移期）仍可用：

- `/flow:aidd-idea-flow` -> `/skill:idea-new`
- `/flow:aidd-research-flow` -> `/skill:researcher`
- `/flow:aidd-plan-flow` -> `/skill:plan-new`
- `/flow:aidd-implement-flow` -> `/skill:implement`
- `/flow:aidd-review-flow` -> `/skill:review`
- `/flow:aidd-qa-flow` -> `/skill:qa`

## Stage Dispatch Runtime 说明

`aidd_runtime/stage_dispatch.py` 负责把宿主命令归一到统一 runtime 入口：

- 归一命令名与 legacy alias。
- 自动解析/注入 `--ticket`（未显式传入时读取 `docs/.active.json`）。
- 自动推进 active feature/stage（调用 `aidd-flow-state` 脚本）。
- `implement/review/qa` 默认执行 preflight gates。
  - 可通过 `AIDD_STAGE_DISPATCH_GATES=0` 临时关闭。

## IDE Profiles 配置

Profile 由 `aidd_runtime/ide_profiles.py` 管理，默认选择顺序：

1. 显式 profile 参数
2. 命令前缀（如 `$aidd:...`）
3. 环境变量 `AIDD_IDE_PROFILE` / `AIDD_HOST`
4. skills 目录自动探测
5. 默认 `kimi`

常用环境变量：

- `AIDD_IDE_PROFILE`: 强制 profile（`kimi|codex|cursor`）
- `AIDD_HOST`: 宿主标识兜底
- `AIDD_SKILLS_DIRS`: 覆盖 skills 搜索目录（`os.pathsep` 分隔）
- `AIDD_PRIMARY_SKILLS_DIR`: 主 skills 目录（由 runtime 注入）

## Hooks 用法

在 **目标项目工作区** 执行（不是插件仓库根目录）：

```bash
python3 $AIDD_ROOT/hooks/gate-workflow.sh
python3 $AIDD_ROOT/hooks/gate-tests.sh
python3 $AIDD_ROOT/hooks/gate-qa.sh
python3 $AIDD_ROOT/hooks/format-and-test.sh
```

说明：

- `gate-workflow.sh`：readiness gates（analyst/research/plan/prd/tasklist/diff）
- `gate-tests.sh`：测试 gate（调用 `format-and-test.sh`）
- `gate-qa.sh`：统一 QA gate 入口

## 开发与测试

```bash
./scripts/test.sh
```

`test.sh` 现为严格模式：Black/Ruff/MyPy/Pytest 任一失败即退出，并输出覆盖率。

## 目录结构

```text
aidd-plugin/
├── aidd_runtime/                # 共享运行时
├── skills/*/runtime/            # 各阶段与共享 runtime
├── hooks/                       # hooks 入口与上下文工具
├── templates/                   # 初始化模板
├── tests/                       # pytest
└── scripts/                     # install/test/verify 等脚本
```

## 文档索引

- 命令速查：`COMMANDS.md`
- 快速上手：`QUICKSTART.md`
- 架构说明：`docs/overview.md`
- 进度计划：`docs/update-plan.md`
- 任务清单：`docs/task-todo-list.md`
