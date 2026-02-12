---
name: aidd-qa-flow
description: |
  AIDD QA 阶段工作流 - 最终质量检查。当审核通过后，
  需要：1) 执行完整测试 2) 检查验收标准 3) 生成 QA 报告时执行此 flow。
type: flow
---

# AIDD QA Flow

执行最终质量检查和验收。

```mermaid
flowchart TD
    A([BEGIN]) --> B[读取 Tasklist 和 AC]
    B --> C[执行完整测试]
    C --> D{测试通过?}
    D -->|否| E[记录失败]
    E --> F[返回 Review]
    D -->|是| G[检查验收标准]
    G --> H{AC 满足?}
    H -->|否| I[记录未满足项]
    I --> F
    H -->|是| J[生成 QA Report]
    J --> K[Stage = done]
    K --> L([END])
```

## 输入

- `aidd/docs/tasklist/{ticket}.md` - 任务清单
- `aidd/docs/prd/{ticket}.prd.md#AIDD:ACCEPTANCE` - 验收标准

## 输出

- `aidd/reports/qa/{ticket}.json` - QA 报告

## 测试策略

- QA 阶段运行完整测试套件
- 对比 AIDD:ACCEPTANCE 检查完成情况

## 完成

```
QA 通过！功能开发完成。
```
