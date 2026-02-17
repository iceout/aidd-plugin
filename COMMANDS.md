# AIDD for Kimi/Codex/Cursor - 命令速查表

## 正确的命令格式

### Flow Skills（执行工作流）

| 命令 | 功能 |
|------|------|
| `/flow:aidd-init-flow` | 初始化 AIDD 工作区 |
| `/flow:aidd-idea-flow` | 创建 PRD 草案 |
| `/flow:aidd-research-flow` | 代码库研究 |
| `/flow:aidd-plan-flow` | 制定实施计划 |
| `/flow:aidd-implement-flow` | 迭代实现代码 |
| `/flow:aidd-review-flow` | 代码审核 |
| `/flow:aidd-qa-flow` | 质量检查 |

### Standard Skills（查看帮助）

| 命令 | 功能 |
|------|------|
| `/skill:aidd-core` | 查看 AIDD 核心文档 |
| `/skill:aidd-research` | 查看研究阶段指南 |
| `/skill:aidd-implementer` | 查看实现者指南 |
| `/skill:aidd-reviewer` | 查看审核者指南 |

## 使用示例

### 完整工作流

```bash
# 1. 进入项目目录
cd my-project

# 2. 启动 Kimi
kimi

# 3. 初始化 AIDD 工作区（首次使用）
> /flow:aidd-init-flow

# 4. 创建新功能
> /flow:aidd-idea-flow FUNC-001 "实现用户登录功能"

# 5. 代码研究（自动生成 RLM）
> /flow:aidd-research-flow FUNC-001

# 6. 制定计划
> /flow:aidd-plan-flow FUNC-001

# 7. 实现代码
> /flow:aidd-implement-flow FUNC-001

# 8. 代码审核
> /flow:aidd-review-flow FUNC-001

# 9. QA 检查
> /flow:aidd-qa-flow FUNC-001
```

### 查看帮助

```bash
# 查看 AIDD 核心概念
> /skill:aidd-core

# 查看研究阶段如何使用 RLM
> /skill:aidd-research

# 查看如何实现代码
> /skill:aidd-implementer
```

## 命名规则说明

- **Skill 名称格式**: `{功能}-{阶段}-flow`（如 `aidd-idea-flow`）
- **Flow 命令**: `/flow:{skill-name}`（如 `/flow:aidd-idea-flow`）
- **Skill 命令**: `/skill:{skill-name}`（如 `/skill:aidd-core`）

## 常见问题

### Q: 为什么不是 `/flow:aidd-idea` 而是 `/flow:aidd-idea-flow`？
A: 为了与 Standard Skills 区分，Flow Skills 的名称包含了 `-flow` 后缀。

### Q: `/skill:aidd-idea-flow` 和 `/flow:aidd-idea-flow` 有什么区别？
A: 
- `/skill:aidd-idea-flow` - 加载 SKILL.md 内容作为提示词（不执行流程）
- `/flow:aidd-idea-flow` - 执行 Mermaid 流程图定义的自动化工作流

### Q: 如何查看有哪些可用的 AIDD 命令？
A: 在 Kimi 中输入 `/` 然后按 Tab 键，可以看到所有可用的斜杠命令。
