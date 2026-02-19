"""Pytest configuration helpers for runtime tests."""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)


def pytest_configure() -> None:  # pragma: no cover - pytest hook
    os.environ.setdefault("AIDD_ROOT", str(PROJECT_ROOT))
