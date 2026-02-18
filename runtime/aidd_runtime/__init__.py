from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Type

_DEBUG_FLAGS = {"1", "true", "yes", "on", "debug"}

_PACKAGE_ROOT = Path(__file__).resolve().parent
_PROJECT_ROOT = _PACKAGE_ROOT.parent.parent  # runtime/aidd_runtime -> runtime -> project_root
_SKILLS_ROOT = _PROJECT_ROOT / "runtime" / "skills"

_runtime_dirs: list[Path] = []
if _SKILLS_ROOT.is_dir():
    for skill_dir in sorted(_SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir():
            continue
        # Support both layouts:
        # - runtime/skills/<skill>/*.py
        # - runtime/skills/<skill>/runtime/*.py
        _runtime_dirs.append(skill_dir)
        skill_runtime = skill_dir / "runtime"
        if skill_runtime.is_dir():
            _runtime_dirs.append(skill_runtime)
_RUNTIME_DIRS = tuple(_runtime_dirs)

# Runtime bridge: resolve `aidd_runtime.<module>` from skills/*/runtime locations
for runtime_dir in _RUNTIME_DIRS:
    if not runtime_dir.is_dir():
        continue
    runtime_dir_str = str(runtime_dir)
    if runtime_dir_str not in __path__:
        __path__.append(runtime_dir_str)


def _debug_enabled() -> bool:
    return os.getenv("AIDD_DEBUG", "").strip().lower() in _DEBUG_FLAGS


def _format_exception_message(exc: BaseException) -> str:
    text = str(exc).strip()
    if not text:
        return exc.__class__.__name__
    return " ".join(chunk.strip() for chunk in text.splitlines() if chunk.strip())


def _aidd_excepthook(exc_type: type[BaseException], exc: BaseException, tb) -> None:
    if _debug_enabled():
        sys.__excepthook__(exc_type, exc, tb)
        return
    message = _format_exception_message(exc)
    sys.stderr.write(f"[aidd] ERROR: {message}\n")


sys.excepthook = _aidd_excepthook
