---
name: aidd-research
description: |
  AIDD 代码研究阶段 - RLM (Research Link Model) 代码库分析。
  当需要：1) 研究现有代码结构 2) 理解模块依赖 3) 查找集成点时触发。
---

# AIDD Research

## RLM (Research Link Model)

RLM 将代码库建模为节点和链接的图结构：
- **Nodes**: 文件/目录的摘要
- **Links**: 代码间的关系（调用、引用）

## 使用流程

1. **生成 RLM 工件**：
```bash
# 生成完整 RLM
python3 $KIMI_AIDD_ROOT/runtime/skills/researcher/runtime/research.py --ticket FUNC-123 --auto

# 按需查询（Slice）
python3 $KIMI_AIDD_ROOT/runtime/skills/aidd-rlm/runtime/rlm_slice.py \
  --ticket FUNC-123 \
  --query "PaymentService"
```

## 阅读顺序

1. `aidd/reports/research/{ticket}-rlm.pack.json` - 主证据包
2. `aidd/docs/research/{ticket}.md` - 研究报告（人工补充）
3. RLM Slice - 针对性查询

## RLM 工件链

```
targets → manifest → worklist → nodes → links → pack
```

## 关键概念

- **Entrypoints**: 模块入口点
- **Hotspots**: 热点代码区域
- **Integration Points**: 系统集成点
- **Risks**: 潜在风险
