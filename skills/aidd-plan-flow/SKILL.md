---
name: aidd-plan-flow
description: |
  AIDD Plan 阶段工作流 - 制定功能实施计划。当完成代码研究后，
  需要：1) 设计技术方案 2) 定义迭代任务 3) 生成 Tasklist 时执行此 flow。
type: flow
---

# AIDD Plan Flow

制定功能的实施计划。

```mermaid
flowchart TD
    A([BEGIN]) --> B[读取 RLM Pack 和 Research]
    B --> C[分析代码结构]
    C --> D[设计技术方案]
    D --> E[定义迭代 I1, I2, I3]
    E --> F[创建 Tasklist]
    F --> G[设置 stage = tasklist]
    G --> H([END])
```

## 输入

- `aidd/reports/research/{ticket}-rlm.pack.json` - RLM 研究证据
- `aidd/docs/research/{ticket}.md` - 研究报告
- `aidd/docs/prd/{ticket}.prd.md` - PRD 文档

## 输出

- `aidd/docs/plan/{ticket}.md` - 实施计划
- `aidd/docs/tasklist/{ticket}.md` - 任务清单

## 下一步

```
计划已制定。下一步执行：/flow:aidd-implement-flow {ticket}
```
