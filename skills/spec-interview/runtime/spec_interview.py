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
from datetime import date
from pathlib import Path

from aidd_runtime import runtime


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ensure spec artifact exists for active ticket and sync template placeholders.",
    )
    parser.add_argument("--ticket", dest="ticket", help="Ticket id (defaults to docs/.active.json).")
    parser.add_argument("--slug-hint", dest="slug_hint", help="Optional slug hint override.")
    parser.add_argument("--spec", dest="spec_path", help="Optional spec path override.")
    return parser.parse_args(argv)


def _replace_placeholders(text: str, ticket: str, slug: str, today: str) -> str:
    return (
        text.replace("<ABC-123>", ticket)
        .replace("<short-slug>", slug)
        .replace("<YYYY-MM-DD>", today)
    )


def _resolve_spec_path(target: Path, override: str | None, ticket: str) -> Path:
    if not override:
        return target / "docs" / "spec" / f"{ticket}.spec.yaml"
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

    plugin_root = runtime.require_plugin_root()
    template_path = plugin_root / "skills" / "spec-interview" / "templates" / "spec.template.yaml"
    if not template_path.exists():
        raise FileNotFoundError(f"spec template not found: {template_path}")
    template_text = template_path.read_text(encoding="utf-8")

    spec_path = _resolve_spec_path(target, getattr(args, "spec_path", None), ticket)
    spec_path.parent.mkdir(parents=True, exist_ok=True)

    created = not spec_path.exists()
    if created:
        rendered = _replace_placeholders(template_text, ticket, slug, today)
        spec_path.write_text(rendered, encoding="utf-8")
    else:
        current = spec_path.read_text(encoding="utf-8")
        updated = _replace_placeholders(current, ticket, slug, today)
        if updated != current:
            spec_path.write_text(updated, encoding="utf-8")

    runtime.maybe_sync_index(target, ticket, slug, reason="spec-interview")
    rel_path = runtime.rel_path(spec_path, target)
    if created:
        print(f"[spec-interview] created {rel_path}")
    else:
        print(f"[spec-interview] synced {rel_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
