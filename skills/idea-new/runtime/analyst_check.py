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

from aidd_runtime.analyst_guard import AnalystValidationError, load_settings, validate_prd

from aidd_runtime import runtime


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate analyst Q/A and PRD readiness for the active feature.",
    )
    parser.add_argument(
        "--ticket",
        dest="ticket",
        help="Ticket identifier to validate (defaults to docs/.active.json).",
    )
    parser.add_argument(
        "--slug-hint",
        dest="slug_hint",
        help="Optional slug hint override (defaults to docs/.active.json).",
    )
    parser.add_argument(
        "--branch",
        help="Current Git branch used to evaluate config.gates analyst branch rules.",
    )
    parser.add_argument(
        "--allow-blocked",
        action="store_true",
        help="Allow PRD with Status: blocked.",
    )
    parser.add_argument(
        "--no-ready-required",
        action="store_true",
        help="Do not require PRD Status: READY.",
    )
    parser.add_argument(
        "--min-questions",
        type=int,
        help="Override minimum required analyst questions.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _, target = runtime.require_workflow_root()
    ticket, context = runtime.require_ticket(
        target,
        ticket=getattr(args, "ticket", None),
        slug_hint=getattr(args, "slug_hint", None),
    )
    settings = load_settings(target)
    try:
        summary = validate_prd(
            target,
            ticket,
            settings=settings,
            branch=args.branch,
            require_ready_override=False if args.no_ready_required else None,
            allow_blocked_override=True if args.allow_blocked else None,
            min_questions_override=args.min_questions,
        )
    except AnalystValidationError as exc:
        raise RuntimeError(str(exc)) from exc

    if summary.status is None:
        print("[aidd] analyst gate disabled; nothing to validate.")
        return 0

    label = runtime.format_ticket_label(context, fallback=ticket)
    print(
        f"[aidd] analyst dialog ready for `{label}` "
        f"(status: {summary.status}, questions: {summary.question_count})."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
