#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HOOK_PREFIX = "[gate-qa]"


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


def main(argv: list[str] | None = None) -> int:
    plugin_root = _bootstrap()
    from hooks import hooklib

    ctx = hooklib.read_hook_context()
    root, _ = hooklib.resolve_project_root(ctx)

    qa_gate_runtime = plugin_root / "skills" / "aidd-core" / "runtime" / "qa_gate.py"
    cmd = [sys.executable, str(qa_gate_runtime)]
    if argv:
        cmd.extend(argv)
    proc = subprocess.run(cmd, cwd=root, check=False)
    return int(proc.returncode)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
