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

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from aidd_runtime import runtime

STATUS_RE = re.compile(r"^\s*Status:\s*([A-Za-z]+)", re.MULTILINE)
CACHE_FILENAME = "prd-check.hash"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate PRD Status: READY.")
    parser.add_argument("--ticket", help="Ticket identifier (defaults to docs/.active.json).")
    parser.add_argument("--prd", help="Override PRD path.")
    return parser.parse_args(argv)


def _resolve_prd_path(project_root: Path, ticket: str, override: str | None) -> Path:
    if override:
        return runtime.resolve_path_for_target(Path(override), project_root)
    return project_root / "docs" / "prd" / f"{ticket}.prd.md"


def _cache_path(root: Path) -> Path:
    return root / ".cache" / CACHE_FILENAME


def _load_cache(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_cache(path: Path, *, ticket: str, hash_value: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"ticket": ticket, "hash": hash_value}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        return


def _hash_prd(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _, project_root = runtime.require_workflow_root()
    ticket, _ = runtime.require_ticket(project_root, ticket=args.ticket, slug_hint=None)

    prd_path = _resolve_prd_path(project_root, ticket, args.prd)
    if not prd_path.exists():
        rel = runtime.rel_path(prd_path, project_root)
        raise SystemExit(f"BLOCK: PRD not found: {rel}")

    text = prd_path.read_text(encoding="utf-8")
    current_hash = _hash_prd(text)
    cache_path = _cache_path(project_root)
    cache_payload = _load_cache(cache_path)
    if cache_payload.get("ticket") == ticket and cache_payload.get("hash") == current_hash:
        print("[prd-check] SKIP: cache hit (reason_code=cache_hit)", file=sys.stderr)
        return 0
    match = STATUS_RE.search(text)
    if not match:
        raise SystemExit("BLOCK: PRD does not contain `Status:` -> set Status: READY before plan-new.")

    status = match.group(1).strip().upper()
    if status != "READY":
        raise SystemExit(
            f"BLOCK: PRD Status: {status} -> set Status: READY before /feature-dev-aidd:plan-new {ticket}."
        )

    print(f"[aidd] PRD ready for `{ticket}` (status: READY).")
    _write_cache(cache_path, ticket=ticket, hash_value=current_hash)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
