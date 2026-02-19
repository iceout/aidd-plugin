# AIDD for Kimi/Codex/Cursor - 快速开始

## 环境准备

```bash
export AIDD_ROOT=<your-path-to-plugin>
./scripts/install.sh
```

## 3 分钟上手

### 1. 进入目标项目并启动 IDE Agent

```bash
cd your-project
```

### 2. 初始化工作区（首次）

```text
> /flow:aidd-init-flow
```

### 3. 执行阶段命令

```text
> /skill:idea-new MY-001 "实现XX功能"
> /skill:researcher MY-001
> /skill:plan-new MY-001
> /skill:review-spec MY-001
> /skill:spec-interview MY-001
> /skill:tasks-new MY-001
> /skill:implement MY-001
> /skill:review MY-001
> /skill:qa MY-001
```

## 核心命令对照

| 你想做 | 输入命令 |
| --- | --- |
| 初始化工作区 | `/flow:aidd-init-flow` |
| 创建新功能 | `/skill:idea-new TICKET "描述"` |
| 研究代码 | `/skill:researcher TICKET` |
| 生成计划 | `/skill:plan-new TICKET` |
| 生成任务清单 | `/skill:tasks-new TICKET` |
| 实现与审查 | `/skill:implement TICKET` / `/skill:review TICKET` |
| QA 验收 | `/skill:qa TICKET` |
| 查看核心说明 | `/skill:aidd-core` |

## 验证安装

```bash
./scripts/verify-flows.sh
```

## 故障排查

1. 命令不存在：重启 IDE，并确认 `~/.config/agents/skills` 下有对应 skill 目录。
2. Python 导入失败：确认 `AIDD_ROOT` 指向插件根目录。
3. 旧 flow 命令仍被调用：改用 `/skill:idea-new` 等 stage skills。

## 下一步

- 详细命令：`COMMANDS.md`
- 项目说明：`README.md`
