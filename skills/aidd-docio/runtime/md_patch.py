#!/usr/bin/env python3
"""Patch markdown by AIDD section or handoff block selector."""

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

import argparse
import json
import sys
from pathlib import Path

from aidd_runtime import runtime
from aidd_runtime.md_slice import parse_ref


def _extract_content(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _patch_section(lines: list[str], section_name: str, content: list[str]) -> list[str]:
    heading = f"## {section_name}"
    start = -1
    for idx, line in enumerate(lines):
        if line.strip() == heading:
            start = idx
            break
    if start < 0:
        raise ValueError(f"section not found: {section_name}")

    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break

    replacement = list(content)
    if replacement and replacement[0].strip().startswith("## "):
        return lines[:start] + replacement + lines[end:]
    return lines[: start + 1] + replacement + lines[end:]


def _patch_handoff(lines: list[str], handoff_id: str, content: list[str]) -> list[str]:
    start = -1
    end = -1
    start_marker = f"<!-- handoff:{handoff_id} start"
    end_marker = f"<!-- handoff:{handoff_id} end"

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if start < 0 and stripped.startswith(start_marker):
            start = idx
            continue
        if start >= 0 and stripped.startswith(end_marker):
            end = idx
            break

    if start < 0:
        raise ValueError(f"handoff start marker not found: {handoff_id}")
    if end < 0:
        raise ValueError(f"handoff end marker not found: {handoff_id}")

    return lines[: start + 1] + content + lines[end:]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Patch markdown by block selector.")
    parser.add_argument("--ref", required=True, help="path.md#AIDD:SECTION or path.md@handoff:<id>")
    parser.add_argument("--content", required=True, help="Path to content file")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        _, target = runtime.require_workflow_root(Path.cwd())

        ref = parse_ref(args.ref)
        source_path = runtime.resolve_path_for_target(Path(ref.source), target)
        if not source_path.exists():
            raise FileNotFoundError(f"source markdown not found: {runtime.rel_path(source_path, target)}")

        content_path = runtime.resolve_path_for_target(Path(args.content), target)
        if not content_path.exists():
            raise FileNotFoundError(f"content file not found: {runtime.rel_path(content_path, target)}")

        lines = source_path.read_text(encoding="utf-8").splitlines()
        content_lines = _extract_content(content_path)

        if ref.kind == "section":
            updated = _patch_section(lines, ref.selector, content_lines)
            selector_label = f"#{ref.selector}"
        else:
            updated = _patch_handoff(lines, ref.selector, content_lines)
            selector_label = f"@handoff:{ref.selector}"

        source_path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")

        payload = {
            "schema": "aidd.md_patch.result.v1",
            "status": "ok",
            "target": runtime.rel_path(source_path, target),
            "selector": selector_label,
            "content": runtime.rel_path(content_path, target),
        }
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"patched={payload['target']}")
            print(f"summary=selector {selector_label} updated")
        return 0
    except Exception as exc:
        print(f"[md-patch] ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
