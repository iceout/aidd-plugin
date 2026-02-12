---
name: aidd-review-flow
description: |
  AIDD Review 阶段工作流 - 代码审核和反馈。当实现完成后，
  需要：1) 检查代码变更 2) 对比 Plan/PRD 3) 生成 Findings 时执行此 flow。
type: flow
---

# AIDD Review Flow

执行代码审核，生成反馈。

```mermaid
flowchart TD
    A([BEGIN]) --> B[收集代码变更]
    B --> C[生成 Review Pack]
    C --> D[执行代码审核]
    D --> E{发现问题?}
    E -->|是| F[生成 Findings]
    F --> G[派生任务]
    G --> H{需要修订?}
    H -->|是| I[Verdict = REVISE]
    I --> J[返回 Implement]
    H -->|否| K[Verdict = SHIP]
    E -->|否| K
    K --> L[Stage = qa]
    L --> M([END])
```

## 输入

- `aidd/reports/loops/{ticket}/{scope_key}.loop.pack.md` - Loop Pack
- `aidd/docs/plan/{ticket}.md` - 实施计划

## 输出

- `aidd/reports/reviewer/{ticket}/{scope_key}.json` - Review Report
- 更新的 Tasklist（添加 handoff 任务）

## Verdict

- **REVISE**: 需要修改，返回 Implement 阶段
- **SHIP**: 审核通过，进入 QA 阶段

## 下一步

```
审核完成。 verdict = SHIP，下一步执行：/flow:aidd-qa-flow {ticket}
```
