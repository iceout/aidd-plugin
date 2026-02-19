# AIDD for Kimi/Codex/Cursor - 命令速查表

## 推荐命令（Stage Skills）

| 命令 | 作用 |
| --- | --- |
| `/flow:aidd-init-flow` | 初始化 AIDD 工作区 |
| `/skill:idea-new <ticket> [note...]` | Idea 阶段：创建/更新 PRD |
| `/skill:researcher <ticket> [--paths ... --keywords ...]` | Research 阶段：生成 RLM 与研究报告 |
| `/skill:plan-new <ticket> [note...]` | Plan 阶段：生成实施计划 |
| `/skill:review-spec <ticket> [note...]` | Review-Spec 阶段：计划/PRD 就绪检查 |
| `/skill:spec-interview <ticket> [note...]` | Spec-Interview 阶段：更新 spec.yaml |
| `/skill:tasks-new <ticket> [note...]` | Tasklist 阶段：生成任务清单 |
| `/skill:implement <ticket> [note...]` | Implement 阶段：执行实现循环 |
| `/skill:review <ticket> [note...]` | Review 阶段：生成 findings |
| `/skill:qa <ticket> [note...]` | QA 阶段：执行质量检查 |

## 兼容别名（迁移期）

以下 `/flow` 入口已保留，但建议优先使用上面的 `/skill` 命令：

| 旧命令 | 新命令 |
| --- | --- |
| `/flow:aidd-idea-flow` | `/skill:idea-new` |
| `/flow:aidd-research-flow` | `/skill:researcher` |
| `/flow:aidd-plan-flow` | `/skill:plan-new` |
| `/flow:aidd-implement-flow` | `/skill:implement` |
| `/flow:aidd-review-flow` | `/skill:review` |
| `/flow:aidd-qa-flow` | `/skill:qa` |

## 常用辅助命令

| 命令 | 作用 |
| --- | --- |
| `/skill:aidd-core` | 核心工作流说明 |
| `/skill:aidd-policy` | 输出/提问/阅读策略约束 |
| `/skill:aidd-reference` | wrapper/runtime 合约参考 |
| `/skill:aidd-stage-research` | 研究阶段证据与交接约束 |

## 完整流程示例

```bash
# 1) 初始化（首次）
> /flow:aidd-init-flow

# 2) Idea -> Research -> Plan
> /skill:idea-new FUNC-001 "实现用户登录功能"
> /skill:researcher FUNC-001
> /skill:plan-new FUNC-001

# 3) Review-Spec -> Tasklist
> /skill:review-spec FUNC-001
> /skill:spec-interview FUNC-001
> /skill:tasks-new FUNC-001

# 4) Loop stages
> /skill:implement FUNC-001
> /skill:review FUNC-001
> /skill:qa FUNC-001
```

## 安装验证

```bash
./scripts/install.sh
./scripts/verify-flows.sh
```

预期：`verify-flows.sh` 输出所有 required stage skills 已安装。
