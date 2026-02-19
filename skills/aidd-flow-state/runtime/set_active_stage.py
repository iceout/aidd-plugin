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
from pathlib import Path

from aidd_runtime import runtime, stage_lexicon
from aidd_runtime.feature_ids import resolve_aidd_root, write_active_state

VALID_STAGES = set(stage_lexicon.CANONICAL_STAGES)
STAGE_ALIASES = dict(stage_lexicon.STAGE_ALIASES)


def _normalize_stage(value: str) -> str:
    return stage_lexicon.resolve_stage_name(value)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Persist the active workflow stage in docs/.active.json.",
    )
    parser.add_argument("stage", help="Stage name to persist.")
    parser.add_argument(
        "--allow-custom",
        action="store_true",
        help="Allow arbitrary stage values (skip validation).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = resolve_aidd_root(Path.cwd())
    stage = _normalize_stage(args.stage)
    if not args.allow_custom and not stage_lexicon.is_known_stage(args.stage, include_aliases=True):
        valid = ", ".join(stage_lexicon.supported_stage_values(include_aliases=True))
        print(f"[stage] invalid stage '{stage}'. Allowed: {valid}.")
        return 2
    write_active_state(root, stage=stage)
    print(f"active stage: {stage}")
    context = runtime.resolve_feature_context(root)
    runtime.maybe_sync_index(root, context.resolved_ticket, context.slug_hint, reason="set-active-stage")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
