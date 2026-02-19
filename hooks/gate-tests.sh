#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HOOK_PREFIX = "[gate-tests]"


def _bootstrap() -> Path:
    raw = os.environ.get("AIDD_ROOT")
    if not raw:
        print(f"{HOOK_PREFIX} AIDD_ROOT is required to run hooks.", file=sys.stderr)
        raise SystemExit(2)
    plugin_root = Path(raw).expanduser().resolve()
    os.environ.setdefault("AIDD_ROOT", str(plugin_root))
    plugin_root_str = str(plugin_root)
    if plugin_root_str not in sys.path:
        sys.path.insert(0, plugin_root_str)
    return plugin_root


def main() -> int:
    plugin_root = _bootstrap()
    script = plugin_root / "hooks" / "format-and-test.sh"
    if not script.exists():
        print(f"{HOOK_PREFIX} missing hook: {script}", file=sys.stderr)
        return 2
    proc = subprocess.run([sys.executable, str(script)], check=False)
    return int(proc.returncode)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
