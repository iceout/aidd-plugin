# Phase 0 – Baseline Assessment Report

> Upstream `ai_driven_dev` root: `/Users/xuanyizhang/code/ai_driven_dev`

## T0.1 – Init Script Validation
- Command: `python3 runtime/skills/aidd-init/runtime/init.py --force` (executed inside `/var/folders/.../tmp.uS8bMxf8pp`).
- Result (initial run): ❌ failed because `runtime/templates/aidd` was missing and plugin root resolved incorrectly.
- Log:
  ```
  [aidd] ERROR: templates not found at /Users/xuanyizhang/code/aidd-plugin/runtime/templates/aidd. Run '/feature-dev-aidd:aidd-init' from the plugin repository.
  ```
- Follow-up (2026-02-16): templates path restored + init script fixed; rerun outputs `copied 32 files` and `.aidd/settings.json` creation.
- Blockers: resolved once templates + seeds moved under `templates/aidd/`.

## T0.2 – Asset Inventory vs. Upstream
| Asset | Status in plugin | Action |
| --- | --- | --- |
| `docs/overview.md` | ✅ 存在，已与 upstream 摸底 | 继续以此版本为基准补充差异 |
| `aidd-plugin与AIDD核心差距分析报告.md` | ✅ 存在 | 持续更新用于追踪缺口 |
| `agents/` | ⚠️ 新建空目录（2026-02-16） | 需要从 upstream 迁移 11 个 Agent |
| `templates/` | ⚠️ 新建空目录（2026-02-16） | 待迁移全量 workspace 模板 |
| `hooks/` | ⚠️ 新建空目录（2026-02-16） | 待迁移自动化脚本 |

> Directories `agents/`, `templates/`, `hooks/` now exist so later phases can sync files without recreating structure.

## T0.3 – Dependency Freeze & Documentation
- `pyproject.toml` now pins runtime deps (`pydantic==2.8.2`, `pyyaml==6.0.1`) and dev tools (`pytest==8.3.2`, `pytest-cov==5.0.0`, `black==24.8.0`, `ruff==0.5.5`, `mypy==1.11.2`).
- `README.md` includes an explicit environment requirements section plus a dependency matrix for quick reference.
- `AGENTS.md` Build/Test section now references the pinned toolchain and instructs contributors to run `uv pip sync pyproject.toml` to stay in lockstep.
