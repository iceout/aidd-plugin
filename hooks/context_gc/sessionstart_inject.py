#!/usr/bin/env python3
from __future__ import annotations


def _bootstrap_entrypoint() -> None:
    import os
    import sys
    from pathlib import Path

    raw_root = os.environ.get("AIDD_ROOT", "").strip()
    plugin_root = None
    if raw_root:
        candidate = Path(raw_root).expanduser()
        if candidate.exists() and (candidate / "aidd_runtime").is_dir():
            plugin_root = candidate.resolve()

    if plugin_root is None:
        current = Path(__file__).resolve()
        for parent in (current.parent, *current.parents):
            if (parent / "aidd_runtime").is_dir():
                plugin_root = parent
                break

    if plugin_root is None:
        raise RuntimeError("Unable to resolve AIDD_ROOT from entrypoint path.")

    os.environ["AIDD_ROOT"] = str(plugin_root)
    plugin_root_str = str(plugin_root)
    if plugin_root_str not in sys.path:
        sys.path.insert(0, plugin_root_str)


_bootstrap_entrypoint()

from hooks.hooklib import (
    load_config,
    read_hook_context,
    resolve_aidd_root,
    resolve_context_gc_mode,
    resolve_project_dir,
    sessionstart_additional_context,
)
from .working_set_builder import build_working_set


def main() -> None:
    ctx = read_hook_context()
    if ctx.hook_event_name != "SessionStart":
        return

    project_dir = resolve_project_dir(ctx)
    aidd_root = resolve_aidd_root(project_dir)
    cfg = load_config(aidd_root)
    if not cfg.get("enabled", True) or not aidd_root:
        return
    if resolve_context_gc_mode(cfg) == "off":
        return

    ws = build_working_set(project_dir)
    if not ws.text.strip():
        return

    sessionstart_additional_context(ws.text)


if __name__ == "__main__":
    main()
