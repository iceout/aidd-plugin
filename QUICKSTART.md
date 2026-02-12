# AIDD for Kimi Code - 快速开始

## 安装（已完成）

```bash
# 环境已配置好
export KIMI_AIDD_ROOT=<your-path-to-plugin>
```

## 3 分钟上手

### 1. 启动 Kimi
```bash
cd your-project
kimi
```

### 2. 初始化（首次）
```
> /flow:aidd-init-flow
```

### 3. 创建功能
```
> /flow:aidd-idea-flow MY-001 "实现XX功能"
```

### 4. 后续流程
```
> /flow:aidd-research-flow MY-001   # 研究代码
> /flow:aidd-plan-flow MY-001       # 制定计划
> /flow:aidd-implement-flow MY-001  # 实现代码
> /flow:aidd-review-flow MY-001     # 代码审核
> /flow:aidd-qa-flow MY-001         # 质量检查
```

## 核心命令对照表

| 你想做 | 输入命令 |
|--------|----------|
| 初始化工作区 | `/flow:aidd-init-flow` |
| 创建新功能 | `/flow:aidd-idea-flow TICKET "描述"` |
| 研究代码 | `/flow:aidd-research-flow TICKET` |
| 写代码 | `/flow:aidd-implement-flow TICKET` |
| 审核代码 | `/flow:aidd-review-flow TICKET` |
| 查看帮助 | `/skill:aidd-core` |

## 故障排除

### 命令不存在？
1. 确认已安装：`ls ~/.config/agents/skills/ | grep aidd`
2. 重启 Kimi CLI

### 环境变量错误？
```bash
export KIMI_AIDD_ROOT=<your-path-to-plugin>
export PYTHONPATH=$KIMI_AIDD_ROOT/runtime:$PYTHONPATH
```

## 下一步

- 阅读完整文档：[README.md](README.md)
- 查看命令详情：[COMMANDS.md](COMMANDS.md)
