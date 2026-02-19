---
name: aidd-reviewer
description: |
  AIDD 审核者角色 - 执行代码审核和生成反馈。当处于 review 阶段，
  需要：1) 检查代码变更 2) 对比 Plan/PRD 3) 生成 Findings 时触发。
---

# AIDD Reviewer

## 输入工件

审核前必须读取：
1. `aidd/reports/loops/{ticket}/{scope_key}/review.latest.pack.md` - Review Pack
2. `aidd/docs/plan/{ticket}.md` - 实施计划
3. `aidd/docs/prd/{ticket}.prd.md` - PRD

## Review Pack 生成

```bash
python3 $AIDD_ROOT/skills/review/runtime/review_pack.py --ticket FUNC-123
```

## Findings 格式

```json
{
  "findings": [
    {
      "id": "F1",
      "severity": "major",
      "category": "logic",
      "description": "缺少空指针检查",
      "recommendation": "添加 null check"
    }
  ]
}
```

## Verdict

- **REVISE**: 需要修改，返回 Implement 阶段
- **SHIP**: 审核通过，进入 QA 阶段

## 审核范围

- 不扩展 Scope
- 新需求 → AIDD:OUT_OF_SCOPE_BACKLOG
- 记录为新的 work_item
