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

from aidd_runtime import readiness_gates, runtime


def parse_args(argv: list[str] | None = None) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        description="Run QA gate with shared readiness-gates facade.",
    )
    parser.add_argument("--ticket", help="Ticket identifier override.")
    parser.add_argument("--slug-hint", dest="slug_hint", help="Optional slug hint override.")
    parser.add_argument("--branch", help="Git branch override.")
    known, extra = parser.parse_known_args(argv)
    return known, extra


def main(argv: list[str] | None = None) -> int:
    args, extra = parse_args(argv)
    _, target = runtime.require_workflow_root()
    ticket, context = runtime.require_ticket(
        target,
        ticket=getattr(args, "ticket", None),
        slug_hint=getattr(args, "slug_hint", None),
    )
    branch = args.branch or runtime.detect_branch(target)

    forwarded = list(extra or [])
    forwarded = [item for item in forwarded if item != "--gate"]

    result = readiness_gates.run_qa_gate(
        target,
        ticket=ticket,
        slug_hint=context.slug_hint or "",
        branch=branch,
        extra_argv=forwarded,
    )
    if result.output:
        if result.returncode == 0:
            sys.stdout.write(result.output + "\n")
        else:
            sys.stderr.write(result.output + "\n")
    return result.returncode


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
