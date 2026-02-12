---
name: aidd-research-flow
description: |
  AIDD Research 阶段工作流 - 代码库研究和 RLM 生成。当 PRD 就绪后，
  需要：1) 分析代码结构 2) 理解依赖关系 3) 生成 RLM 证据时执行此 flow。
type: flow
---

# AIDD Research Flow

研究代码库结构，生成 RLM (Research Link Model)。

```mermaid
flowchart TD
    A([BEGIN]) --> B[读取 PRD 和 Research Hints]
    B --> C[生成 RLM Targets]
    C --> D[生成 RLM Manifest]
    D --> E[生成 RLM Worklist]
    E --> F[构建 Nodes 和 Links]
    F --> G[生成 RLM Pack]
    G --> H[设置 stage = plan]
    H --> I([END])
```

## 输入

- `aidd/docs/prd/{ticket}.prd.md` - PRD 文档
- `aidd/docs/prd/{ticket}.prd.md#AIDD:RESEARCH_HINTS` - 研究提示

## 输出

- `aidd/reports/research/{ticket}-rlm.pack.json` - RLM 证据包
- `aidd/docs/research/{ticket}.md` - 研究报告

## 关键命令

```bash
# 生成完整 RLM
python3 $KIMI_AIDD_ROOT/runtime/skills/researcher/runtime/research.py --ticket {ticket} --auto
```

## 下一步

```
研究完成。下一步执行：/flow:aidd-plan-flow {ticket}
```
