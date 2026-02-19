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


from aidd_runtime import prd_review, runtime


def main(argv: list[str] | None = None) -> int:
    args = prd_review.parse_args(argv)
    _, target = runtime.require_workflow_root()
    exit_code = prd_review.run(args)
    if exit_code == 0:
        context = runtime.resolve_feature_context(
            target,
            ticket=getattr(args, "ticket", None),
            slug_hint=getattr(args, "slug_hint", None),
        )
        ticket = (context.resolved_ticket or "").strip()
        if ticket:
            slug_hint = (context.slug_hint or ticket).strip() or ticket
            runtime.maybe_sync_index(target, ticket, slug_hint, reason="prd-review")
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
