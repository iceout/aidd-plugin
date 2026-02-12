---
name: aidd-core
description: |
  AIDD (AI-Driven Development) 核心工作流框架。当用户需要：1) 启动结构化软件开发流程
  2) 在 idea/research/plan/implement/review/qa 阶段间导航 3) 管理功能开发的生命周期时触发。
  提供 AIDD 的基础概念、工作流说明和常用命令参考。
---

# AIDD Core

## 概述

AIDD 是一个 AI 驱动的结构化软件开发工作流：

```
Idea → Research → Plan → Review-Spec → Tasklist → Implement → Review → QA
```

## 核心概念

### Ticket
功能的唯一标识符（如 `FUNC-123`）。所有工件以此命名：
- `aidd/docs/prd/FUNC-123.prd.md` - PRD 文档
- `aidd/reports/research/FUNC-123-rlm.pack.json` - 研究证据

### Stage
当前工作流阶段，存储在 `aidd/docs/.active.json`：
- `idea`: 创建 PRD 草案
- `research`: 代码库研究（RLM）
- `plan`: 制定实施计划
- `implement`: 迭代实现
- `review`: 代码审核
- `qa`: 质量检查

### Work Item
具体的工作单元：
- `I1`, `I2`, `I3`... - 实现迭代
- `review:F1`, `review:F2`... - 审核发现的问题

## 常用命令

### 环境设置
```bash
# 激活开发环境
source $KIMI_AIDD_ROOT/scripts/activate.sh
```

### 状态管理
```bash
# 设置活动功能
python3 $KIMI_AIDD_ROOT/runtime/skills/aidd-flow-state/runtime/set_active_feature.py FUNC-123

# 设置当前阶段
python3 $KIMI_AIDD_ROOT/runtime/skills/aidd-flow-state/runtime/set_active_stage.py implement

# 诊断环境
python3 $KIMI_AIDD_ROOT/runtime/skills/aidd-observability/runtime/doctor.py
```

### RLM 研究
```bash
# 生成 RLM Pack
python3 $KIMI_AIDD_ROOT/runtime/skills/aidd-rlm/runtime/rlm_slice.py --ticket FUNC-123 --query "PaymentService"
```

## Flow Skills

- `/flow:aidd-init-flow` - 初始化 AIDD 工作区
- `/flow:aidd-idea-flow` - 启动 Idea 阶段
- `/flow:aidd-research-flow` - 启动 Research 阶段
- `/flow:aidd-plan-flow` - 启动 Plan 阶段
- `/flow:aidd-implement-flow` - 启动 Implement 阶段
- `/flow:aidd-review-flow` - 启动 Review 阶段
- `/flow:aidd-qa-flow` - 启动 QA 阶段

## 输出合约

所有 AIDD 命令遵循统一输出格式：
```
Status: READY|WARN|BLOCKED
Ticket: FUNC-123
Artifacts updated:
- aidd/docs/.../file.md
Next actions:
- /flow:aidd-research-flow FUNC-123
```

## 快速开始

1. **初始化工作区**（首次使用）：
   ```
   /flow:aidd-init-flow
   ```

2. **开始新功能**：
   ```
   /flow:aidd-idea-flow FUNC-001 "实现用户登录功能"
   ```

3. **继续开发**：
   ```
   /flow:aidd-implement-flow FUNC-001
   ```

## 目录结构

```
aidd/
├── docs/
│   ├── .active.json          # 当前状态
│   ├── prd/                  # PRD 文档
│   ├── plan/                 # 实施计划
│   ├── research/             # 研究报告
│   ├── tasklist/             # 任务清单
│   └── spec/                 # 技术规范
├── reports/
│   ├── research/             # RLM 证据
│   ├── loops/                # Loop Pack
│   ├── reviewer/             # 审核报告
│   └── qa/                   # QA 报告
└── config/
    ├── gates.json            # 门控配置
    └── conventions.json      # 约定配置
```
