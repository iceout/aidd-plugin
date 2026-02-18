#!/usr/bin/env python3
"""Validate AIDD context maps (readmap/writemap)."""

from __future__ import annotations

def _bootstrap_entrypoint() -> None:
    import os
    import sys
    from pathlib import Path

    raw_root = os.environ.get("AIDD_ROOT", "").strip()
    plugin_root = None
    if raw_root:
        candidate = Path(raw_root).expanduser()
        if candidate.exists():
            plugin_root = candidate.resolve()

    if plugin_root is None:
        current = Path(__file__).resolve()
        for parent in (current.parent, *current.parents):
            runtime_dir = parent / "runtime"
            if (runtime_dir / "aidd_runtime").is_dir():
                plugin_root = parent
                break

    if plugin_root is None:
        raise RuntimeError("Unable to resolve AIDD_ROOT from entrypoint path.")

    os.environ["AIDD_ROOT"] = str(plugin_root)
    for entry in (plugin_root / "runtime", plugin_root):
        entry_str = str(entry)
        if entry_str not in sys.path:
            sys.path.insert(0, entry_str)


_bootstrap_entrypoint()

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from aidd_runtime import aidd_schemas, stage_lexicon

SCHEMA_READMAP = "aidd.readmap.v1"
SCHEMA_WRITEMAP = "aidd.writemap.v1"
SUPPORTED_SCHEMA_VERSIONS = tuple(sorted({SCHEMA_READMAP, SCHEMA_WRITEMAP}))
VALID_STAGES = set(stage_lexicon.supported_stage_values(include_aliases=True))


class ValidationError(ValueError):
    pass


def _is_str(value: Any) -> bool:
    return isinstance(value, str)


def _require_fields(obj: dict[str, Any], fields: Iterable[str], errors: list[str], *, prefix: str = "") -> None:
    for field in fields:
        if field not in obj:
            errors.append(f"{prefix}missing field: {field}")


def _validate_str_list(value: Any, errors: list[str], *, field: str) -> None:
    if not isinstance(value, list):
        errors.append(f"field {field} must be list[str]")
        return
    for idx, item in enumerate(value):
        if not _is_str(item):
            errors.append(f"{field}[{idx}] must be string")


def _validate_readmap(payload: dict[str, Any], errors: list[str]) -> None:
    _require_fields(
        payload,
        (
            "schema",
            "ticket",
            "stage",
            "scope_key",
            "work_item_key",
            "generated_at",
            "entries",
            "allowed_paths",
            "loop_allowed_paths",
        ),
        errors,
    )
    _validate_str_list(payload.get("allowed_paths"), errors, field="allowed_paths")
    _validate_str_list(payload.get("loop_allowed_paths"), errors, field="loop_allowed_paths")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        errors.append("field entries must be list")
    else:
        for idx, entry in enumerate(entries):
            prefix = f"entries[{idx}]"
            if not isinstance(entry, dict):
                errors.append(f"{prefix} must be object")
                continue
            _require_fields(entry, ("ref", "path", "selector", "required", "reason"), errors, prefix=f"{prefix}.")
            for key in ("ref", "path", "selector", "reason"):
                if key in entry and not _is_str(entry.get(key)):
                    errors.append(f"{prefix}.{key} must be string")
            if "required" in entry and not isinstance(entry.get("required"), bool):
                errors.append(f"{prefix}.required must be boolean")


def _validate_writemap(payload: dict[str, Any], errors: list[str]) -> None:
    _require_fields(
        payload,
        (
            "schema",
            "ticket",
            "stage",
            "scope_key",
            "work_item_key",
            "generated_at",
            "allowed_paths",
            "loop_allowed_paths",
            "docops_only_paths",
            "always_allow",
        ),
        errors,
    )
    _validate_str_list(payload.get("allowed_paths"), errors, field="allowed_paths")
    _validate_str_list(payload.get("loop_allowed_paths"), errors, field="loop_allowed_paths")
    _validate_str_list(payload.get("docops_only_paths"), errors, field="docops_only_paths")
    _validate_str_list(payload.get("always_allow"), errors, field="always_allow")
    write_blocks = payload.get("write_blocks")
    if write_blocks is not None and not isinstance(write_blocks, list):
        errors.append("field write_blocks must be list when provided")


def validate_context_map_data(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["payload must be a JSON object"]

    schema = payload.get("schema")
    if schema not in SUPPORTED_SCHEMA_VERSIONS:
        values = ", ".join(sorted(SUPPORTED_SCHEMA_VERSIONS))
        errors.append(f"schema must be one of: {values}")
        return errors

    for key in ("ticket", "stage", "scope_key", "work_item_key", "generated_at"):
        if key in payload and not _is_str(payload.get(key)):
            errors.append(f"field {key} must be string")
    stage = str(payload.get("stage") or "")
    if stage and not stage_lexicon.is_known_stage(stage, include_aliases=True):
        errors.append(f"invalid stage: {stage}")

    if schema == SCHEMA_READMAP:
        _validate_readmap(payload, errors)
    elif schema == SCHEMA_WRITEMAP:
        _validate_writemap(payload, errors)

    return errors


def load_context_map(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValidationError(f"cannot read context map file: {path}") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in context map file: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationError("context map payload must be JSON object")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate AIDD readmap/writemap payload.")
    parser.add_argument("--map", dest="map_path", help="Path to readmap.json or writemap.json")
    parser.add_argument("--quiet", action="store_true", help="Suppress OK output")
    parser.add_argument(
        "--print-supported-versions",
        action="store_true",
        help="Print supported schema versions and exit.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.print_supported_versions:
        values = ",".join(
            list(aidd_schemas.supported_schema_versions("aidd.readmap.v"))
            + list(aidd_schemas.supported_schema_versions("aidd.writemap.v"))
        )
        print(values)
        return 0

    if not args.map_path:
        print("[context-map-validate] ERROR: --map is required unless --print-supported-versions is used", file=sys.stderr)
        return 2

    path = Path(args.map_path)
    try:
        payload = load_context_map(path)
    except ValidationError as exc:
        print(f"[context-map-validate] ERROR: {exc}", file=sys.stderr)
        return 2

    errors = validate_context_map_data(payload)
    if errors:
        for err in errors:
            print(f"[context-map-validate] ERROR: {err}", file=sys.stderr)
        return 2

    if not args.quiet:
        schema = payload.get("schema")
        print(f"[context-map-validate] OK: {path} ({schema})")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
