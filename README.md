# AIDD for Kimi Code

AIDD (AI-Driven Development) 插件移植到 Kimi Code CLI。

## 快速开始

### 1. 环境设置

```bash
cd <your-path-to-plugin>
source scripts/activate.sh
```

### 2. 安装 Skills

```bash
./scripts/install.sh
```

### 3. 设置环境变量

添加到 `~/.bashrc` 或 `~/.zshrc`：

```bash
export KIMI_AIDD_ROOT=<your-path-to-plugin>
```

### 4. 验证安装

```bash
export PYTHONPATH=$KIMI_AIDD_ROOT/runtime:$PYTHONPATH
python3 $KIMI_AIDD_ROOT/runtime/skills/aidd-observability/runtime/doctor.py
```

### 5. 在 Kimi 中使用

```
/skill:aidd-core
/flow:aidd-init-flow
/flow:aidd-idea-flow FUNC-001 "实现用户登录功能"
```

## 开发状态

### ✅ Phase 0: 环境准备
- [x] 项目目录结构
- [x] Python 3.13 虚拟环境 (UV)
- [x] 开发辅助脚本

### ✅ Phase 1: 核心运行时迁移
- [x] 复制 AIDD Runtime 代码
- [x] 替换环境变量 (CLAUDE_ → KIMI_)
- [x] 基础测试通过

### ✅ Phase 2: Skills 创建 (核心)
- [x] aidd-core (Standard Skill)
- [x] aidd-init-flow (Flow Skill)
- [x] aidd-idea-flow (Flow Skill)
- [x] aidd-implement-flow (Flow Skill)
- [x] aidd-research, aidd-implementer, aidd-reviewer

### 🔄 Phase 3: 初始化系统 (进行中)
- [ ] 完善 init.py
- [ ] 创建工作区模板

### ⏳ Phase 4: 测试和文档
- [ ] 端到端测试
- [ ] 完整文档

## 项目结构

```
kimi-aidd-plugin/
├── runtime/
│   ├── aidd_runtime/          # 核心运行时包
│   └── skills/                # 各阶段运行时
│       ├── aidd-core/
│       ├── aidd-flow-state/
│       ├── aidd-docio/
│       ├── aidd-rlm/
│       ├── aidd-loop/
│       ├── aidd-observability/
│       ├── aidd-init/
│       ├── researcher/
│       ├── implement/
│       ├── review/
│       └── qa/
├── skills/                    # Kimi Skills
│   ├── aidd-core/SKILL.md
│   ├── aidd-init-flow/SKILL.md
│   ├── aidd-idea-flow/SKILL.md
│   ├── aidd-implement-flow/SKILL.md
│   └── ...
├── tests/
├── scripts/
│   ├── activate.sh
│   ├── install.sh
│   └── test.sh
└── pyproject.toml
```

## 可用的 Flow Skills

- `/flow:aidd-init-flow` - 初始化 AIDD 工作区
- `/flow:aidd-idea-flow` - 创建 PRD 草案
- `/flow:aidd-research-flow` - 代码库研究 (RLM)
- `/flow:aidd-plan-flow` - 制定实施计划
- `/flow:aidd-implement-flow` - 迭代实现代码
- `/flow:aidd-review-flow` - 代码审核
- `/flow:aidd-qa-flow` - 质量检查

## 技术栈

- Python 3.13+
- UV (包管理)
- Pydantic (数据验证)
- PyYAML (配置解析)

## 许可证

MIT
