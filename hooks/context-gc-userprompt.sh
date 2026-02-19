#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path


def _bootstrap() -> None:
    raw = os.environ.get("AIDD_ROOT")
    if not raw:
        print("[context-gc-userprompt] AIDD_ROOT is required to run hooks.", file=sys.stderr)
        raise SystemExit(2)
    plugin_root = Path(raw).expanduser().resolve()
    os.environ.setdefault("AIDD_ROOT", str(plugin_root))
    plugin_root_str = str(plugin_root)
    if plugin_root_str not in sys.path:
        sys.path.insert(0, plugin_root_str)


def main() -> int:
    _bootstrap()
    from hooks.context_gc import userprompt_guard

    result = userprompt_guard.main()
    if isinstance(result, int):
        return result
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
