# 目录收敛最小迁移清单（P1.2）

> 日期：2026-02-18  
> 目标：在 `P1.3` 中一次性完成目录收敛，消除双层 `runtime/skills` 布局和路径桥接。

## 1. 目标单一布局（向 upstream 靠拢）

目标形态（唯一标准）：

```text
<repo>/
├── aidd_runtime/                # 共享运行时包（顶层包）
├── skills/
│   ├── <skill>/SKILL.md
│   ├── <skill>/runtime/*.py
│   ├── <skill>/templates/*
│   └── <skill>/references/*
├── hooks/
├── templates/
├── tests/
└── scripts/
```

约束：

- 运行脚本命令统一使用 `${AIDD_ROOT}/skills/<skill>/runtime/<tool>.py`。
- 入口脚本仅依赖 `AIDD_ROOT`，不要求手工设置 `PYTHONPATH`。
- 删除目录桥接逻辑，不保留 `skills/*` 兼容层。

## 2. 迁移范围快照（当前仓库）

- `skills/` 下 Python 文件：79 个。
- `aidd_runtime/` 下 Python 文件：10 个。
- 含路径/环境变量相关引用文件（`runtime/skills`、`aidd_runtime`、`PYTHONPATH`）：30 个。

## 3. 移动路径清单（Move Map）

### 3.1 共享运行时包

- `aidd_runtime/*.py` → `aidd_runtime/*.py`

### 3.2 技能运行时代码

- `skills/aidd-core/runtime/*` → `skills/aidd-core/runtime/*`
- `skills/aidd-core/reports/*` → `skills/aidd-core/runtime/reports/*`
- `skills/aidd-core/schemas/*` → `skills/aidd-core/schemas/*`
- `skills/aidd-init/runtime/*` → `skills/aidd-init/runtime/*`
- `skills/aidd-observability/runtime/*` → `skills/aidd-observability/runtime/*`
- `skills/<skill>/*.py`（无 runtime 子目录）→ `skills/<skill>/runtime/*.py`  
  适用：`aidd-docio`, `aidd-flow-state`, `aidd-loop`, `aidd-rlm`, `implement`, `qa`, `researcher`, `review`

### 3.3 目标目录补齐

- 为 `skills/implement`, `skills/qa`, `skills/researcher`, `skills/review` 创建标准目录骨架（至少 `runtime/`）。
- `SKILL.md` 迁移由 `T3.1` 负责；`P1.3` 只保证 runtime 路径可用。

## 4. 导入与加载调整清单

### 4.1 包加载逻辑

- 重写 `aidd_runtime/__init__.py`，删除基于 `runtime/skills` 的动态 `__path__` bridge，并改为显式追加 `skills/*/runtime`（或静态导入策略）来解析 `aidd_runtime.<module>`。

### 4.2 入口自举逻辑

- 所有入口 `_bootstrap_entrypoint()` 的路径探测从“查找 `<repo>/aidd_runtime`”改为“查找 `<repo>/aidd_runtime`”。
- `sys.path` 注入目标改为 `<repo>`（必要时保留 `<repo>/skills/*/runtime` 的运行时注入实现，但不再依赖 `<repo>/runtime`）。

### 4.3 字符串路径改写规则

- `skills/<skill>/runtime/<tool>.py` → `skills/<skill>/runtime/<tool>.py`
- `skills/<skill>/<tool>.py` → `skills/<skill>/runtime/<tool>.py`
- `aidd_runtime` → `aidd_runtime`

## 5. 命令文本更新范围

必须改写的文件类型：

- 文档：`README.md`, `QUICKSTART.md`, `COMMANDS.md`, `AGENTS.md`, `docs/*.md`
- 技能说明：`skills/*/SKILL.md`
- Hook 与守卫：`hooks/*.sh`, `hooks/context_gc/*.py`
- Runtime 内提示文案：`runtime/**`（迁移后为 `skills/**/runtime/**` 与 `aidd_runtime/**`）
- 测试与脚本：`tests/**`, `scripts/test.sh`

关键命令标准化：

- 移除文档里的 `export PYTHONPATH=...` 前置步骤。
- 医生脚本与各 flow 示例全部改为新路径。

## 6. 执行批次（P1.3 可直接照此实施）

1. 批次 A：结构迁移
- 新建目标目录并移动文件（保持文件内容不变）。
- 确保 `skills/*/runtime` 下模块完整可导入。

2. 批次 B：代码改写
- 一次性替换路径字符串、入口探测逻辑、`aidd_runtime` bridge。
- 删除旧路径 fallback 和兼容分支。

3. 批次 C：文档与脚本改写
- 统一命令文本、测试覆盖路径、安装/诊断说明。

4. 批次 D：烟测与收尾
- 运行 `init/research/qa/hook` smoke tests（对应 P1.4）。
- 通过后删除空目录 `runtime/skills` 与 `runtime/aidd_runtime`。

## 7. 回滚点设计

- `R0`（迁移前）：基线 tag/commit（建议 `checkpoint/p1.3-r0`）。
- `R1`（仅完成批次 A）：若导入失败，可直接 `git revert <R1_commit>`。
- `R2`（批次 B+C 完成）：若命令文本或 hook 回归，回滚到 `R1`。
- `R3`（批次 D 完成）：作为 `P1.3` 交付点。

回滚原则：

- 禁止手工拣文件回退；只用 commit 粒度回滚，避免半迁移状态。
- 每个批次独立提交，提交信息包含批次编号（A/B/C/D）。

## 8. 完成判定（Definition of Done）

- 仓库内不再存在 `skills/` 与 `aidd_runtime/` 作为代码源目录。
- 仓库内不再出现运行命令路径前缀 `skills/`。
- 文档不再要求用户手工设置 `PYTHONPATH`。
- `aidd-init`, `research`, `qa`, `gate-workflow` 在新路径下 smoke 通过。
