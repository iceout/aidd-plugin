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
import sys
from datetime import date
from pathlib import Path

from aidd_runtime import runtime, tasklist_check


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ensure tasklist exists for active ticket and run tasklist validation.",
    )
    parser.add_argument("--ticket", dest="ticket", help="Ticket id (defaults to docs/.active.json).")
    parser.add_argument("--slug-hint", dest="slug_hint", help="Optional slug hint override.")
    parser.add_argument("--tasklist", dest="tasklist_path", help="Optional tasklist path override.")
    parser.add_argument(
        "--force-template",
        action="store_true",
        help="Rewrite tasklist from template even if file already exists.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero if tasklist-check returns error.",
    )
    return parser.parse_args(argv)


def _replace_placeholders(text: str, ticket: str, slug: str, today: str, scope_key: str) -> str:
    return (
        text.replace("<ABC-123>", ticket)
        .replace("<short-slug>", slug)
        .replace("<YYYY-MM-DD>", today)
        .replace("<scope_key>", scope_key)
    )


def _resolve_tasklist_path(target: Path, override: str | None, ticket: str) -> Path:
    if not override:
        return target / "docs" / "tasklist" / f"{ticket}.md"
    candidate = Path(override)
    if candidate.is_absolute():
        return candidate
    return runtime.resolve_path_for_target(candidate, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _, target = runtime.require_workflow_root()
    ticket, context = runtime.require_ticket(
        target,
        ticket=getattr(args, "ticket", None),
        slug_hint=getattr(args, "slug_hint", None),
    )
    slug = (context.slug_hint or ticket).strip() or ticket
    today = date.today().isoformat()
    scope_key = runtime.resolve_scope_key(work_item_key=None, ticket=ticket)

    plugin_root = runtime.require_plugin_root()
    template_path = plugin_root / "skills" / "tasks-new" / "templates" / "tasklist.template.md"
    if not template_path.exists():
        raise FileNotFoundError(f"tasklist template not found: {template_path}")
    template_text = template_path.read_text(encoding="utf-8")

    tasklist_path = _resolve_tasklist_path(target, getattr(args, "tasklist_path", None), ticket)
    tasklist_path.parent.mkdir(parents=True, exist_ok=True)

    created = not tasklist_path.exists()
    if created or args.force_template:
        rendered = _replace_placeholders(template_text, ticket, slug, today, scope_key)
        tasklist_path.write_text(rendered, encoding="utf-8")
    else:
        current = tasklist_path.read_text(encoding="utf-8")
        updated = _replace_placeholders(current, ticket, slug, today, scope_key)
        if updated != current:
            tasklist_path.write_text(updated, encoding="utf-8")

    result = tasklist_check.check_tasklist(target, ticket)
    rel_path = runtime.rel_path(tasklist_path, target)
    print(f"[tasks-new] tasklist: {rel_path}")
    if result.status == "ok":
        print("[tasks-new] tasklist-check: ok")
    elif result.status == "warn":
        print("[tasks-new] tasklist-check: warn", file=sys.stderr)
        for detail in result.details or []:
            print(f"[tasks-new] {detail}", file=sys.stderr)
    elif result.status == "error":
        print("[tasks-new] tasklist-check: error", file=sys.stderr)
        print(f"[tasks-new] {result.message}", file=sys.stderr)
        for detail in result.details or []:
            print(f"[tasks-new] {detail}", file=sys.stderr)
        if args.strict:
            return result.exit_code()
    else:
        print(f"[tasks-new] tasklist-check: {result.status}")

    runtime.maybe_sync_index(target, ticket, slug, reason="tasks-new")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
