# Repository Guidelines

## Project Structure & Module Organization
This plugin is organized around runtime code, reusable skills, and contributor tooling. `aidd_runtime/` hosts shared Python runtime modules, and stage runtimes live under `skills/*/runtime/` (RLM, loop, flow state, docio, QA, etc.). `skills/` also contains public SKILL.md definitions for stage commands (for example `/skill:idea-new`, `/skill:plan-new`, `/skill:implement`) plus legacy flow aliases (for example `/flow:aidd-idea-flow`), while `scripts/` stores helper automation and `tests/` holds pytest suites and fixtures. Stable docs (`README.md`, `COMMANDS.md`, `QUICKSTART.md`, `docs/overview.md`, `docs/adoption-codex-cursor-kimi.md`) describe runtime usage and multi-IDE adoption; keep new specs beside them for visibility.

## Build, Test, and Development Commands
Run `source scripts/activate.sh` to enter the UV-backed Python 3.13 environment, then install/refresh dependencies with `./scripts/install.sh`. Validate the CLI glue with `python3 skills/aidd-observability/runtime/doctor.py` after adjusting `AIDD_ROOT`. Use `./scripts/test.sh` for the full gate (Black, Ruff, MyPy, pytest with coverage) and `./scripts/verify-flows.sh` to ensure every flow SKILL is synced into `~/.config/agents/skills/`.

> Dependency policy: runtime relies on pinned wheels (pydantic 2.8.2, PyYAML 6.0.1) and the dev toolchain locks pytest 8.3.2, pytest-cov 5.0.0, black 24.8.0, ruff 0.5.5, and mypy 1.11.2. Run `uv pip sync pyproject.toml` whenever you pull to keep the tool versions consistent across IDEs.

## Coding Style & Naming Conventions
Python modules target 3.13, use 4-space indentation, and embrace typing with `disallow_untyped_defs = true` in MyPy. Prefer `snake_case` for functions, `PascalCase` for classes, and prefix flow assets with their phase (e.g., `aidd-plan-flow`). Format with `black --line-length 100`, lint with `ruff check aidd_runtime/ skills/ hooks/ tests/` (rule set E,F,W,I,N,D,UP,B,C4,SIM), and keep imports sorted automatically. Keep docstrings imperative and limit Markdown line width to roughly 100 characters for diff clarity.

## Testing Guidelines
Place new unit tests in `tests/` mirroring the runtime path (e.g., `tests/runtime/test_resources.py`). Name functions `test_<behavior>` and parametrize when covering scenario matrices. Execute `pytest tests/ -v --cov=aidd_runtime --cov-report=term-missing` (already wrapped inside `scripts/test.sh`) and ensure warnings stay clean. Add golden-data fixtures under `tests/data/` when needed; prefer deterministic inputs instead of network calls.

## Commit & Pull Request Guidelines
Use Conventional Commits to flag scope and impact (e.g., `feat(runtime): add qa gate hooks`, `chore(scripts): harden install`). Each pull request should describe context, link the tracked ticket (FUNC-###), summarize testing output, and include screenshots or log excerpts for CLI flows. Keep diffs limited to a single SDLC stage when possible, and update related SKILL.md or documentation whenever runtime contracts change. Request review once `./scripts/test.sh` passes locally.

## Environment & Configuration Tips
Set `export AIDD_ROOT=/path/to/aidd-plugin` during development sessions. Workspace artifacts live under `./aidd/` once flows run; clean them between tickets to avoid leaking stale packs. When working across IDEs (Kimi, Cursor, Codex CLI), verify that updated skills are reinstalled before invoking `/flow:` commands to prevent dispatch mismatches.
