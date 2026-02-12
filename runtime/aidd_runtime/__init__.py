from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Type


_DEBUG_FLAGS = {"1", "true", "yes", "on", "debug"}

_PACKAGE_ROOT = Path(__file__).resolve().parent
_PROJECT_ROOT = _PACKAGE_ROOT.parent.parent  # runtime/aidd_runtime -> runtime -> project_root

_RUNTIME_DIRS = (
    _PROJECT_ROOT / "runtime" / "skills" / "aidd-core" / "runtime",
    _PROJECT_ROOT / "runtime" / "skills" / "aidd-docio" / "runtime",
    _PROJECT_ROOT / "runtime" / "skills" / "aidd-flow-state" / "runtime",
    _PROJECT_ROOT / "runtime" / "skills" / "aidd-observability" / "runtime",
    _PROJECT_ROOT / "runtime" / "skills" / "aidd-loop" / "runtime",
    _PROJECT_ROOT / "runtime" / "skills" / "aidd-rlm" / "runtime",
    _PROJECT_ROOT / "runtime" / "skills" / "aidd-init" / "runtime",
    _PROJECT_ROOT / "runtime" / "skills" / "researcher" / "runtime",
    _PROJECT_ROOT / "runtime" / "skills" / "implement" / "runtime",
    _PROJECT_ROOT / "runtime" / "skills" / "review" / "runtime",
    _PROJECT_ROOT / "runtime" / "skills" / "qa" / "runtime",
)

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


def _aidd_excepthook(exc_type: Type[BaseException], exc: BaseException, tb) -> None:
    if _debug_enabled():
        sys.__excepthook__(exc_type, exc, tb)
        return
    message = _format_exception_message(exc)
    sys.stderr.write(f"[aidd] ERROR: {message}\n")


sys.excepthook = _aidd_excepthook
