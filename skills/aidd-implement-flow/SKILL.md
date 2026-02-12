---
name: aidd-implement-flow
description: |
  AIDD Implement 阶段工作流 - 按照 Tasklist 迭代实现代码。当进入实现阶段，
  需要：1) 读取 Loop Pack 2) 执行代码修改 3) 记录进度时执行此 flow。
type: flow
---

# AIDD Implement Flow

迭代实现功能的代码。

```mermaid
flowchart TD
    A([BEGIN]) --> B[读取 .active.json 状态]
    B --> C{当前阶段?}
    C -->|非 implement| D[提示错误]
    D --> Z([END])
    C -->|implement| F[读取 tasklist]
    F --> G[获取当前工作项]
    G --> H[生成 Loop Pack]
    H --> I[读取 Loop Pack]
    I --> J[执行代码实现]
    J --> K[生成 Actions]
    K --> L[应用 Actions]
    L --> M{还有更多工作项?}
    M -->|是| N[更新 work_item]
    N --> H
    M -->|否| O[Stage = review]
    O --> Z
```

## Loop Pack 阅读顺序

1. `aidd/reports/loops/{ticket}/{scope_key}.loop.pack.md`
2. `aidd/docs/tasklist/{ticket}.md`
3. `aidd/reports/research/{ticket}-rlm.pack.json`

## Actions 系统

实现完成后生成 Actions JSON：

```json
{
  "actions": [
    {
      "type": "tasklist_ops.set_iteration_done",
      "params": {"item_id": "I1", "kind": "iteration"}
    },
    {
      "type": "tasklist_ops.append_progress_log",
      "params": {
        "date": "2026-02-12",
        "source": "implement",
        "item_id": "I1",
        "kind": "iteration",
        "hash": "abc123",
        "msg": "完成支付模块重构"
      }
    }
  ]
}
```

应用 Actions：
```bash
python3 $KIMI_AIDD_ROOT/runtime/skills/aidd-docio/runtime/actions_apply.py \
  --actions aidd/reports/actions/{ticket}/{scope_key}/implement.actions.json
```

## Loop 纪律

- 每次只完成一个工作项
- 不扩展 scope（新需求 → AIDD:OUT_OF_SCOPE_BACKLOG）
- 不提问（有问题 → handoff）
- 测试遵循阶段策略（implement 阶段不运行测试）
