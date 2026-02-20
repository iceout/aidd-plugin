from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import ModuleType

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_hook_module(module_name: str, rel_path: str) -> ModuleType:
    path = PROJECT_ROOT / rel_path
    loader = SourceFileLoader(module_name, str(path))
    spec = importlib.util.spec_from_loader(module_name, loader)
    if spec is None:
        raise RuntimeError(f"failed to create module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module
