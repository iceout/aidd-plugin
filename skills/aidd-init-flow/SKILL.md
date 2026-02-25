---
name: aidd-init-flow
description: |
  AIDD 工作区初始化 Flow。当用户首次在项目中使用 AIDD，
  需要：1) 创建 aidd/ 目录结构 2) 复制模板文件 3) 设置初始配置时执行。
type: flow
---

# AIDD Init Flow

初始化 AIDD 工作区。

```mermaid
flowchart TD
    A([BEGIN]) --> B[检查当前目录是否已初始化]
    B --> C{已初始化?}
    C -->|是| D[询问是否覆盖]
    D --> E{用户确认?}
    E -->|否| Z([END])
    E -->|是| G[备份现有配置]
    C -->|否| G
    G --> H[创建目录结构]
    H --> I[复制模板文件]
    I --> J[创建 .active.json]
    J --> K[完成]
    K --> Z
```

## 创建的目录结构

```
aidd/
├── AGENTS.md
├── config/
│   ├── gates.json
│   ├── conventions.json
│   └── context_gc.json
├── docs/
│   ├── .active.json
│   ├── prd/
│   ├── plan/
│   ├── research/
│   ├── tasklist/
│   └── spec/
└── reports/
    ├── actions/
    ├── context/
    ├── loops/
    ├── qa/
    ├── research/
    ├── reviewer/
    └── tests/
```

## 使用方法

用户执行：
```
/aidd-init-flow
```

或者带参数强制覆盖：
```
/aidd-init-flow --force
```

## 初始化后

提示用户：
```
AIDD 工作区已初始化！

下一步：
1. 创建新功能：/skill:idea-new TICKET-001 "功能描述"
2. 或查看文档：cat aidd/AGENTS.md
```
