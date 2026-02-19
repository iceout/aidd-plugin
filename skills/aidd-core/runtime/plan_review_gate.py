#!/usr/bin/env python3
"""Shared plan review gate logic for Claude workflow hooks.

Checks that docs/plan/<ticket>.md contains a `## Plan Review` section with
Status READY and no open action items.
"""

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
import re
from collections.abc import Iterable
from pathlib import Path

from aidd_runtime import gates
from aidd_runtime.feature_ids import resolve_aidd_root

DEFAULT_APPROVED = {"ready"}
DEFAULT_BLOCKING = {"blocked"}
REVIEW_HEADER = "## Plan Review"
ACTION_ITEMS_HEADER = "action items"
FENCE_PREFIXES = ("```", "~~~")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate plan review readiness.")
    parser.add_argument("--ticket", required=True, help="Active feature ticket.")
    parser.add_argument("--file-path", default="", help="Path being modified.")
    parser.add_argument("--branch", default="", help="Current branch name.")
    parser.add_argument(
        "--config",
        default="config/gates.json",
        help="Path to gates configuration file (default: config/gates.json).",
    )
    parser.add_argument(
        "--skip-on-plan-edit",
        action="store_true",
        help="Return success when the plan file itself is being edited.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def detect_project_root(target: Path | None = None) -> Path:
    return resolve_aidd_root(target or Path.cwd())


def normalize_path(raw: str, root: Path) -> str:
    if not raw:
        return ""
    candidate = Path(raw)
    if candidate.is_absolute():
        try:
            normalized = candidate.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            normalized = candidate.as_posix()
    else:
        normalized = candidate.as_posix()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.lstrip("/")


def parse_review_section(content: str) -> tuple[bool, str, list[str]]:
    inside = False
    found = False
    status = ""
    action_items: list[str] = []
    fallback_items: list[str] = []
    inside_action_items = False
    saw_action_items = False
    inside_fence = False

    for raw in content.splitlines():
        stripped = raw.strip()
        if stripped.startswith("## "):
            if stripped == REVIEW_HEADER:
                inside = True
                found = True
                inside_action_items = False
                saw_action_items = False
                inside_fence = False
                continue
            if inside:
                break
            continue
        if not inside:
            continue

        if stripped.startswith(FENCE_PREFIXES):
            inside_fence = not inside_fence
            continue
        if inside_fence:
            continue

        if stripped.startswith("### "):
            heading = re.sub(r"[-_]+", " ", stripped[4:].strip().lower())
            inside_action_items = heading == ACTION_ITEMS_HEADER
            if inside_action_items:
                saw_action_items = True
            continue

        lower = stripped.lower()
        if lower.startswith("status:"):
            raw_value = stripped.split(":", 1)[1].strip()
            match = re.match(r"([a-z]+)", raw_value, flags=re.IGNORECASE)
            status = match.group(1).lower() if match else raw_value.lower()
            continue

        if stripped.startswith("- ["):
            if inside_action_items:
                action_items.append(stripped)
            elif not saw_action_items:
                fallback_items.append(stripped)

    if not saw_action_items:
        action_items = fallback_items

    return found, status, action_items


def run_gate(args: argparse.Namespace) -> int:
    root = detect_project_root()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path
    try:
        gate = gates.load_gate_section(config_path, "plan_review")
    except ValueError:
        gate = {}

    enabled = bool(gate.get("enabled", True))
    if not enabled:
        return 0

    if gates.matches(gate.get("skip_branches"), args.branch):
        return 0
    branches = gate.get("branches")
    if branches and not gates.matches(branches, args.branch):
        return 0

    ticket = args.ticket.strip()
    plan_path = root / "docs" / "plan" / f"{ticket}.md"
    if not plan_path.is_file():
        print(f"BLOCK: missing plan (docs/plan/{ticket}.md) -> run /feature-dev-aidd:plan-new {ticket}")
        return 1

    normalized = normalize_path(args.file_path, root)
    if args.skip_on_plan_edit and normalized.endswith(f"docs/plan/{ticket}.md"):
        return 0

    content = plan_path.read_text(encoding="utf-8")
    found, status, action_items = parse_review_section(content)

    allow_missing = bool(gate.get("allow_missing_section", False))
    if not found:
        if allow_missing:
            return 0
        print(f"BLOCK: missing section '## Plan Review' in docs/plan/{ticket}.md -> run /feature-dev-aidd:review-spec {ticket}")
        return 1

    approved: set[str] = {str(item).lower() for item in gate.get("approved_statuses", DEFAULT_APPROVED)}
    blocking: set[str] = {str(item).lower() for item in gate.get("blocking_statuses", DEFAULT_BLOCKING)}

    if status in blocking:
        print(f"BLOCK: Plan Review is marked '{status.upper()}' -> resolve blockers via /feature-dev-aidd:review-spec {ticket}")
        return 1

    if approved and status not in approved:
        print(f"BLOCK: Plan Review is not READY (Status: {status.upper() or 'PENDING'}) -> run /feature-dev-aidd:review-spec {ticket}")
        return 1

    if bool(gate.get("require_action_items_closed", True)):
        for item in action_items:
            if item.startswith("- [ ]"):
                print(f"BLOCK: Plan Review still has open action items -> update docs/plan/{ticket}.md")
                return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(run_gate(parse_args()))
