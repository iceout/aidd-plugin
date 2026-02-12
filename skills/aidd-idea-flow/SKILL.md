---
name: aidd-idea-flow
description: |
  AIDD Idea 阶段工作流 - 创建 PRD 草案和收集需求。当用户想要开始一个新功能开发，
  需要：1) 定义功能范围 2) 创建 PRD 文档 3) 澄清需求问题时执行此 flow。
type: flow
---

# AIDD Idea Flow

创建功能的 PRD（Product Requirements Document）草案。

```mermaid
flowchart TD
    A([BEGIN]) --> B[接收用户的功能描述]
    B --> C[设置 active feature]
    C --> D[设置 stage = idea]
    D --> E[创建 PRD 模板]
    E --> F[分析需求生成问题]
    F --> G{有未回答问题?}
    G -->|是| H[向用户提问]
    H --> I[接收回答]
    I --> F
    G -->|否| J[检查 PRD 就绪状态]
    J --> K{检查通过?}
    K -->|否| L[标记 BLOCKED]
    L --> H
    K -->|是| M[更新 stage = research]
    M --> N[提示下一步]
    N --> O([END])
```

## 输入

用户提供：
- Ticket ID（如 `FUNC-123`）
- 功能描述（如 "实现购物车优惠券功能"）

## 输出

生成的工件：
- `aidd/docs/prd/{ticket}.prd.md` - PRD 文档
- `aidd/docs/.active.json` - 更新活动状态

## 问题格式

向用户提问时使用标准格式：

```
Question N (Blocker|Clarification): ...
Why: ...
Options: A) ... B) ...
Default: ...
```

用户回答格式：
```markdown
## AIDD:ANSWERS
- Answer 1: ...
- Answer 2: ...
```

## 下一步

Flow 结束后，提示用户：
```
PRD 草案已创建。下一步执行：/flow:aidd-research {ticket}
```
