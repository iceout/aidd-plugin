"""Pytest configuration helpers for runtime tests."""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = PROJECT_ROOT / "runtime"

if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))


def pytest_configure() -> None:  # pragma: no cover - pytest hook
    os.environ.setdefault("AIDD_ROOT", str(PROJECT_ROOT))
