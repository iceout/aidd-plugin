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

from pathlib import Path

from hooks.hooklib import (
    load_config,
    read_hook_context,
    resolve_aidd_root,
    resolve_context_gc_mode,
    resolve_project_dir,
)
from .working_set_builder import build_working_set


def _safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_latest(aidd_root: Path, ws_text: str, ticket: str | None) -> None:
    reports_dir = aidd_root / "reports" / "context"
    _safe_mkdir(reports_dir)
    (reports_dir / "latest_working_set.md").write_text(ws_text + "\n", encoding="utf-8")

    if ticket:
        ticket_root = reports_dir / "by-ticket" / ticket
        _safe_mkdir(ticket_root)
        (ticket_root / "latest_working_set.md").write_text(ws_text + "\n", encoding="utf-8")


def main() -> None:
    ctx = read_hook_context()
    if ctx.hook_event_name not in ("Stop", "SubagentStop"):
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

    _write_latest(aidd_root, ws.text, ws.ticket)


if __name__ == "__main__":
    main()
