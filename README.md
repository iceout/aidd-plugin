# AIDD for Kimi/Codex/Cursor

AIDD (AI-Driven Development) 插件移植到 Kimi/Codex/Cursor。

## 快速开始

### 1. 环境设置

```bash
cd <your-path-to-plugin>
source scripts/activate.sh
```

### 2. 安装 Skills

```bash
./scripts/install.sh
```
Cursor/Codex 都不支持 `.config/agents/skills`,
Codex 需要 `ln -s ~/.config/agents/skills ~/.codex/skills/custom_skills`
Cursor 需要 `rsync -avL --delete ~/.config/agents/skills/ ~/.cursor/skills/`

### 3. 设置环境变量

添加到 `~/.bashrc` 或 `~/.zshrc`：

```bash
export AIDD_ROOT=<your-path-to-plugin>
```

### 4. 验证安装

```bash
python3 $AIDD_ROOT/skills/aidd-observability/runtime/doctor.py
```

### 5. 在 Kimi/Codex/Cursor 中使用

```
/skill:aidd-core
/flow:aidd-init-flow
/skill:idea-new FUNC-001 "实现用户登录功能"
```

## 开发环境要求

- Python 3.13.x（推荐通过 `uv` 提供的虚拟环境管理）。
- `pyproject.toml` 中所有依赖均已锁定，使用 `uv pip sync pyproject.toml` 可还原。
- 当前固定依赖：

| 分组 | 包 | 版本 |
| --- | --- | --- |
| runtime | pydantic | 2.8.2 |
| runtime | pyyaml | 6.0.1 |
| dev | pytest | 8.3.2 |
| dev | pytest-cov | 5.0.0 |
| dev | black | 24.8.0 |
| dev | ruff | 0.5.5 |
| dev | mypy | 1.11.2 |

> 通过固定版本，我们可以在多个 IDE/CLI（Kimi、Cursor、Codex）之间获得可重复的 lint/test 结果。

## 目录收敛结果（P1.3 / P1.4）

- 运行时代码已收敛为单一布局：`aidd_runtime/` + `skills/*/runtime/`。
- 旧目录 `runtime/skills` 与 `runtime/aidd_runtime` 已移除。
- 运行入口与 hooks 已统一使用 `AIDD_ROOT` 自举，不再依赖手工 `PYTHONPATH`。
- 已新增迁移烟测：`tests/runtime/test_layout_migration_smoke.py`（覆盖 init / research / qa / hook）。

烟测执行示例：

```bash
.venv/bin/pytest -q tests/runtime/test_layout_migration_smoke.py
```

### 已知风险

- `research`/`rlm_targets` 在缺少 `AIDD:RESEARCH_HINTS` 时会按设计阻断，这属于业务前置条件，不是导入错误。
- `qa --skip-tests` 会把测试记录为 `skipped`，可能掩盖本地依赖缺失（如 Python 包、工具链）问题。
- `gate-qa` 在插件仓库根目录执行会被工作区保护机制阻断；应在目标项目工作区执行。

## 开发状态

### ✅ Phase 0: 环境准备
- [x] 项目目录结构
- [x] Python 3.13 虚拟环境 (UV)
- [x] 开发辅助脚本

### ✅ Phase 1: 核心运行时迁移
- [x] 复制 AIDD Runtime 代码
- [x] 替换环境变量 (CLAUDE_ → AIDD_)
- [x] 基础测试通过

### ✅ Phase 2: Skills 创建 (核心)
- [x] aidd-core (Standard Skill)
- [x] aidd-init-flow (Flow Skill)
- [x] implement / review / qa / researcher (Stage Skills)
- [x] idea-new / plan-new / tasks-new / review-spec / spec-interview
- [x] aidd-policy / aidd-reference / aidd-stage-research (Shared Skills)

### ✅ Phase 3: Stage & Shared Skills
- [x] 以 stage commands 替换旧 flow 文档入口（保留兼容别名）
- [x] 引入共享策略技能：aidd-policy / aidd-reference / aidd-stage-research
- [x] 安装脚本改为仅安装包含 SKILL.md 的目录，并补充验证脚本

### ⏳ Phase 4: 测试和文档
- [ ] 端到端测试
- [ ] 完整文档

## 项目结构

```
aidd-plugin/
├── aidd_runtime/              # 共享运行时包
├── skills/                    # Skills
│   ├── aidd-core/
│   │   ├── SKILL.md
│   │   └── runtime/
│   ├── aidd-init-flow/SKILL.md
│   ├── idea-new/SKILL.md
│   ├── plan-new/SKILL.md
│   ├── tasks-new/SKILL.md
│   ├── review-spec/SKILL.md
│   ├── spec-interview/SKILL.md
│   ├── implement/SKILL.md
│   ├── review/SKILL.md
│   ├── qa/SKILL.md
│   ├── aidd-rlm/runtime/
│   ├── aidd-loop/runtime/
│   ├── aidd-flow-state/runtime/
│   ├── aidd-docio/runtime/
│   └── ...
│   └── ...
├── tests/
├── scripts/
│   ├── activate.sh
│   ├── install.sh
│   └── test.sh
└── pyproject.toml
```

## 可用命令技能

- `/flow:aidd-init-flow` - 初始化 AIDD 工作区
- `/skill:idea-new` - 创建 PRD 草案
- `/skill:researcher` - 代码库研究 (RLM)
- `/skill:plan-new` - 制定实施计划
- `/skill:review-spec` - 审核计划与 PRD
- `/skill:spec-interview` - 规格访谈（可选）
- `/skill:tasks-new` - 生成任务清单
- `/skill:implement` - 迭代实现代码
- `/skill:review` - 代码审核
- `/skill:qa` - 质量检查

兼容别名（迁移期保留）：`/flow:aidd-idea-flow`、`/flow:aidd-research-flow`、`/flow:aidd-plan-flow`、`/flow:aidd-implement-flow`、`/flow:aidd-review-flow`、`/flow:aidd-qa-flow`。

## 技术栈

- Python 3.13+
- UV (包管理)
- Pydantic (数据验证)
- PyYAML (配置解析)

## 许可证

MIT
