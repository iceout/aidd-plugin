#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

HOOK_PREFIX = "[gate-workflow]"


def _bootstrap() -> None:
    raw = os.environ.get("AIDD_ROOT")
    if not raw:
        print(f"{HOOK_PREFIX} AIDD_ROOT is required to run hooks.", file=sys.stderr)
        raise SystemExit(2)
    plugin_root = Path(raw).expanduser().resolve()
    os.environ.setdefault("AIDD_ROOT", str(plugin_root))
    plugin_root_str = str(plugin_root)
    if plugin_root_str not in sys.path:
        sys.path.insert(0, plugin_root_str)

    vendor_dir = plugin_root / "hooks" / "_vendor"
    if vendor_dir.exists():
        sys.path.insert(0, str(vendor_dir))


def main() -> int:
    _bootstrap()
    from aidd_runtime import gate_workflow as tools_module

    return tools_module.main()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
