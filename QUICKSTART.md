# AIDD Quickstart (Kimi/Cursor/Codex)

## 0. 一次性准备

在插件仓库执行：

```bash
cd /path/to/aidd-plugin
source scripts/activate.sh

# 安装到已存在的 skills 目录
./scripts/install.sh
# 或按 IDE 安装
./scripts/install.sh --ide codex --ide cursor

export AIDD_ROOT=/path/to/aidd-plugin
./scripts/verify-flows.sh
```

## 1. 在目标项目初始化

```bash
cd /path/to/your-project
```

在 IDE 对话里执行：

```text
/aidd-init-flow
```

## 2. 跑通主链路

```text
/skill:idea-new DEMO-001 "实现一个最小功能"
/skill:researcher DEMO-001
/skill:plan-new DEMO-001
/skill:tasks-new DEMO-001
/skill:implement DEMO-001
/skill:review DEMO-001
/skill:qa DEMO-001
```

## 3. IDE Profile 关键点

- Kimi/Cursor：通常使用 `/skill:...`
- Codex：通常使用 `$aidd:...`（也兼容 `/skill:...`）
- 如需强制 profile：

```bash
export AIDD_IDE_PROFILE=codex   # kimi|codex|cursor
```

- 如需覆盖 skills 搜索目录：

```bash
export AIDD_SKILLS_DIRS="$HOME/.codex/skills:$HOME/.cursor/skills"
```

## 4. Hooks（可选）

在目标项目工作区执行：

```bash
python3 $AIDD_ROOT/hooks/gate-workflow.sh
python3 $AIDD_ROOT/hooks/gate-tests.sh
python3 $AIDD_ROOT/hooks/gate-qa.sh
```

## 5. 常见问题

1. `ticket is required`：先执行 `idea-new <ticket>`，或显式传 `--ticket`。
2. `AIDD_ROOT is required`：确认已 `export AIDD_ROOT=...`。
3. 找不到命令：重启 IDE 后再执行 `./scripts/install.sh` + `./scripts/verify-flows.sh`。
4. QA 报测试 skipped：补齐目标项目依赖后重跑 `qa`。

## 参考

- `README.md`
- `COMMANDS.md`
- `docs/overview.md`
