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

from aidd_runtime.research_guard import ResearchValidationError, load_settings, validate_research

from aidd_runtime import runtime


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate researcher report readiness for the active feature.",
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
        help="Current Git branch used to evaluate config.gates researcher branch rules.",
    )
    return parser.parse_args(argv)


def _materialize_plan_doc(target: Path, ticket: str) -> tuple[Path | None, bool]:
    plugin_root = runtime.require_plugin_root()
    template_path = plugin_root / "skills" / "plan-new" / "templates" / "plan.template.md"
    if not template_path.exists():
        return None, False

    plan_path = target / "docs" / "plan" / f"{ticket}.md"
    if plan_path.exists():
        return plan_path, False

    content = template_path.read_text(encoding="utf-8").replace("<ticket>", ticket)
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(content, encoding="utf-8")
    return plan_path, True


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
        summary = validate_research(
            target,
            ticket,
            settings=settings,
            branch=args.branch,
        )
    except ResearchValidationError as exc:
        raise RuntimeError(str(exc)) from exc

    if summary.status is None:
        if summary.skipped_reason:
            print(f"[aidd] research gate skipped ({summary.skipped_reason}).")
        else:
            print("[aidd] research gate disabled; nothing to validate.")
    else:
        label = runtime.format_ticket_label(context, fallback=ticket)
        details = [f"status: {summary.status}"]
        if summary.path_count is not None:
            details.append(f"paths: {summary.path_count}")
        if summary.age_days is not None:
            details.append(f"age: {summary.age_days}d")
        print(f"[aidd] research gate OK for `{label}` ({', '.join(details)}).")

    plan_path, created = _materialize_plan_doc(target, ticket)
    if plan_path is not None:
        rel = runtime.rel_path(plan_path, target)
        if created:
            print(f"[aidd] plan scaffold created at {rel}.")
        else:
            print(f"[aidd] plan scaffold already exists at {rel}.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
