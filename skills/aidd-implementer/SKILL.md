---
name: aidd-implementer
description: |
  AIDD 实现者角色 - 按照 Tasklist 执行代码实现。当处于 implement 阶段，
  需要：1) 读取 Loop Pack 2) 执行代码修改 3) 记录 Actions 时触发。
---

# AIDD Implementer

## 输入工件

实现前必须读取：
1. `aidd/reports/loops/{ticket}/{scope_key}.loop.pack.md` - Loop Pack
2. `aidd/docs/tasklist/{ticket}.md` - Tasklist
3. `aidd/research/{ticket}.md` - 研究上下文

## Loop Pack 结构

```markdown
## Work Item
- Ticket: FUNC-123
- Scope Key: I1
- Title: 重构支付模块

## Goal
实现支付模块的核心重构

## Boundaries
- Allowed: src/payment/**
- Forbidden: src/checkout/CartService.kt

## DoD
- [ ] PaymentService 接口定义完成
- [ ] Stripe 适配器实现
```

## Actions 系统

实现完成后，生成 Actions：

```json
{
  "actions": [
    {
      "type": "tasklist_ops.set_iteration_done",
      "params": {"item_id": "I1", "kind": "iteration"}
    }
  ]
}
```

## Loop 纪律

1. **读取顺序**: Loop Pack → Review Pack → Context Pack
2. **禁止提问**: 有问题记录为 handoff
3. **禁止扩展 Scope**: 新需求 → OUT_OF_SCOPE_BACKLOG
4. **最小修改**: 只改必要的代码
