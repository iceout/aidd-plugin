# Codex/Cursor/Kimi Adoption Guide

## 1. 适用范围

本指南仅面向本项目支持的三类宿主工具：Codex、Cursor、Kimi。

目标：给出统一可执行的采用路径，避免把插件逻辑与历史 Claude 工作流绑定。

## 2. 安装目录与命令前缀

| 工具 | skills 默认目录 | 常用命令前缀 | 备注 |
| --- | --- | --- | --- |
| Kimi | `~/.config/agents/skills` | `/skill:` | 默认 profile 为 `kimi` |
| Cursor | `~/.cursor/skills` | `/skill:` | 与 Kimi 同类前缀 |
| Codex | `~/.codex/skills` | `$aidd:` 或 `/skill:` | `$aidd:` 可直接触发 codex profile 识别 |

## 3. 推荐安装流程

在插件仓库执行：

```bash
source scripts/activate.sh
export AIDD_ROOT=/path/to/aidd-plugin

# 安装到单个或多个 IDE
./scripts/install.sh --ide codex --ide cursor --ide kimi

# 校验安装
./scripts/verify-flows.sh
```

如果你只想安装到一个目录，也可使用：

```bash
./scripts/install.sh --target ~/.codex/skills
```

## 4. 阶段命令对照

推荐阶段命令（跨工具统一）：

```text
/flow:aidd-init-flow
/skill:idea-new <ticket> "需求"
/skill:researcher <ticket>
/skill:plan-new <ticket>
/skill:tasks-new <ticket>
/skill:implement <ticket>
/skill:review <ticket>
/skill:qa <ticket>
```

Codex 可选写法：

```text
$aidd:idea-new <ticket> "需求"
$aidd:researcher <ticket>
$aidd:plan-new <ticket>
```

说明：legacy `/flow:aidd-*-flow` 仍有兼容映射，但建议使用 `/skill:*`。

## 5. IDE Profile 与环境变量

`aidd_runtime/ide_profiles.py` 的默认选择顺序：

1. 显式 profile 参数
2. 命令前缀信号（如 `$aidd:`）
3. `AIDD_IDE_PROFILE` / `AIDD_HOST`
4. skills 目录自动探测
5. 默认 `kimi`

常用变量：

- `AIDD_ROOT`：插件根目录（必需）
- `AIDD_IDE_PROFILE`：强制 profile（`kimi|codex|cursor`）
- `AIDD_HOST`：宿主标识兜底
- `AIDD_SKILLS_DIRS`：覆盖 skills 搜索目录（多个路径用 `:` 分隔）

示例：

```bash
export AIDD_ROOT=/path/to/aidd-plugin
export AIDD_IDE_PROFILE=codex
export AIDD_SKILLS_DIRS="$HOME/.codex/skills:$HOME/.cursor/skills"
```

## 6. 常见问题排查

### 6.1 命令不存在 / 找不到 skill

1. 重新执行 `./scripts/install.sh --ide <tool>`
2. 执行 `./scripts/verify-flows.sh`
3. 重启 IDE 会话

### 6.2 运行时报 `AIDD_ROOT is required`

确认当前 shell/IDE 环境已设置：

```bash
export AIDD_ROOT=/path/to/aidd-plugin
```

### 6.3 报 `ticket is required`

- 先执行 `idea-new <ticket>` 建立 active state，或
- 直接在命令里传 `--ticket <ticket>`

### 6.4 QA 显示 tests skipped

这是工作区依赖不足或调用了 `--skip-tests`；先补齐项目依赖，再重跑 `qa`。

### 6.5 Hooks 执行异常

`gate-workflow/gate-tests/gate-qa` 应在目标项目工作区执行，不应在插件仓库根目录执行。

## 7. 相关文档

- `README.md`
- `QUICKSTART.md`
- `COMMANDS.md`
- `docs/overview.md`
- `docs/p4.2-ide-profiles.md`
