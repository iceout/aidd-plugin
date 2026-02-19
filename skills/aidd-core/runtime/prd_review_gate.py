#!/usr/bin/env python3
"""Shared PRD review gate logic for Claude workflow hooks.

The script checks that `docs/prd/<ticket>.prd.md` contains a `## PRD Review`
section with a READY status and no unresolved action items. Review runs after
plan review and blocks implementation until ready. Behaviour is
configured through `config/gates.json` (see the `prd_review` section).

Exit codes:
    0 — gate passed or skipped (disabled / branch excluded / direct PRD edit).
    1 — gate failed (message is printed to stdout).
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
import json
from collections.abc import Iterable
from pathlib import Path

from aidd_runtime import gates
from aidd_runtime.feature_ids import resolve_aidd_root

DEFAULT_APPROVED = {"ready"}
DEFAULT_BLOCKING = {"blocked"}
DEFAULT_BLOCKING_SEVERITIES = {"critical"}
DEFAULT_CODE_PREFIXES = (
    "src/",
    "tests/",
    "test/",
    "app/",
    "services/",
    "backend/",
    "frontend/",
    "lib/",
    "core/",
    "packages/",
    "modules/",
    "cmd/",
)
REVIEW_HEADER = "## PRD Review"
DIALOG_HEADER = "## Dialog analyst"



def feature_label(ticket: str, slug_hint: str | None = None) -> str:
    ticket_value = ticket.strip()
    hint = (slug_hint or "").strip()
    if not ticket_value:
        return ""
    if hint and hint != ticket_value:
        return f"{ticket_value} (slug hint: {hint})"
    return ticket_value


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate PRD review readiness.")
    parser.add_argument(
        "--ticket",
        "--slug",
        dest="ticket",
        required=True,
        help="Active feature ticket (alias: --slug).",
    )
    parser.add_argument(
        "--slug-hint",
        dest="slug_hint",
        default="",
        help="Optional slug hint used for messaging (defaults to docs/.active.json).",
    )
    parser.add_argument(
        "--file-path",
        default="",
        help="Path being modified (used to skip checks for direct PRD edits).",
    )
    parser.add_argument(
        "--branch",
        default="",
        help="Current branch name for branch-based filters.",
    )
    parser.add_argument(
        "--config",
        default="config/gates.json",
        help="Path to gates configuration file (default: config/gates.json).",
    )
    parser.add_argument(
        "--skip-on-prd-edit",
        action="store_true",
        help="Return success when the PRD file itself is being edited.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def _normalize_file_path(raw: str, root: Path) -> str:
    if not raw:
        return ""
    try:
        rel = Path(raw).resolve().relative_to(root.resolve())
        normalized = rel.as_posix()
    except Exception:
        normalized = raw.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.lstrip("/")


def _normalize_items(values: Iterable[str] | None, *, suffix: str = "") -> list[str]:
    result: list[str] = []
    for item in values or ():
        text = str(item or "").strip()
        if not text:
            continue
        text = text.replace("\\", "/")
        while text.startswith("./"):
            text = text[2:]
        text = text.lstrip("/")
        if suffix and not text.endswith(suffix):
            text = f"{text}{suffix}"
        result.append(text)
    return result


def _is_code_path(path: str, prefixes: Iterable[str], globs: Iterable[str]) -> bool:
    normalized = path.replace("\\", "/")
    if not normalized:
        return False
    for prefix in prefixes:
        if normalized.startswith(prefix):
            return True
    for pattern in globs:
        if fnmatch(normalized, pattern):
            return True
    return False


def parse_review_section(content: str) -> tuple[bool, str, list[str]]:
    inside = False
    found = False
    status = ""
    action_items: list[str] = []
    for raw in content.splitlines():
        stripped = raw.strip()
        if stripped.startswith("## "):
            inside = stripped == REVIEW_HEADER
            if inside:
                found = True
            continue
        if not inside:
            continue
        lower = stripped.lower()
        if lower.startswith("status:"):
            status = stripped.split(":", 1)[1].strip().lower()
        elif stripped.startswith("- ["):
            action_items.append(stripped)
    return found, status, action_items


def _resolve_report_path(root: Path, template: str) -> Path:
    report_path = Path(template)
    if not report_path.is_absolute():
        parts = report_path.parts
        if parts and parts[0] == "aidd" and root.name == "aidd":
            report_path = Path(*parts[1:])
        report_path = root / report_path
    return report_path


def _inflate_columnar(section: object) -> list[dict]:
    if not isinstance(section, dict):
        return list(section) if isinstance(section, list) else []
    cols = section.get("cols")
    rows = section.get("rows")
    if not isinstance(cols, list) or not isinstance(rows, list):
        return []
    inflated: list[dict] = []
    for row in rows:
        if not isinstance(row, list):
            continue
        inflated.append({str(col): row[idx] if idx < len(row) else None for idx, col in enumerate(cols)})
    return inflated


def format_message(
    kind: str,
    ticket: str,
    slug_hint: str | None = None,
    status: str | None = None,
    report_status: str | None = None,
) -> str:
    label = feature_label(ticket, slug_hint)
    human_status = (status or "PENDING").upper()
    if kind == "missing_section":
        return (
            f"BLOCK: missing section '## PRD Review' in aidd/docs/prd/{ticket}.prd.md -> run /feature-dev-aidd:review-spec {label} after review-plan"
        )
    if kind == "missing_prd":
        return (
            f"BLOCK: PRD is missing or incomplete -> open docs/prd/{ticket}.prd.md, complete the dialog, and finish /feature-dev-aidd:review-spec {label or ticket}."
        )
    if kind == "blocking_status":
        return (
            f"BLOCK: PRD Review is marked '{human_status}' -> resolve blockers and update status via /feature-dev-aidd:review-spec {label or ticket}"
        )
    if kind == "status_mismatch":
        report_label = (report_status or "PENDING").upper()
        return (
            f"BLOCK: PRD Review status in report ({report_label}) does not match PRD ({human_status}) -> "
            f"rerun /feature-dev-aidd:review-spec {label or ticket}"
        )
    if kind == "not_approved":
        return f"BLOCK: PRD Review is not READY (Status: {human_status}) -> run /feature-dev-aidd:review-spec {label or ticket}"
    if kind == "open_actions":
        return (
            f"BLOCK: PRD Review still has open action items -> move them to docs/tasklist/{ticket}.md and track completion."
        )
    if kind == "missing_report":
        return f"BLOCK: missing PRD Review report (aidd/reports/prd/{ticket}.json) -> rerun /feature-dev-aidd:review-spec {label or ticket}"
    if kind == "report_corrupted":
        return f"BLOCK: PRD Review report is corrupted -> regenerate via /feature-dev-aidd:review-spec {label or ticket}"
    if kind == "blocking_finding":
        return (
            f"BLOCK: PRD Review report contains critical findings -> address them and update report for {label or ticket}."
        )
    if kind == "draft_dialog":
        return (
            f"BLOCK: PRD status is draft -> complete section '{DIALOG_HEADER}', set Status: READY, then run /feature-dev-aidd:review-spec {label or ticket}."
        )
    return f"BLOCK: PRD Review is not ready -> run /feature-dev-aidd:review-spec {label or ticket}"


def detect_project_root(target: Path | None = None) -> Path:
    return resolve_aidd_root(target or Path.cwd())


def extract_dialog_status(content: str) -> str | None:
    inside = False
    for raw in content.splitlines():
        stripped = raw.strip()
        lower = stripped.lower()
        if lower.startswith(DIALOG_HEADER.lower()):
            inside = True
            continue
        if inside and stripped.startswith("## "):
            break
        if inside and lower.startswith("status:"):
            return stripped.split(":", 1)[1].strip().lower()
    return None


def run_gate(args: argparse.Namespace) -> int:
    root = detect_project_root()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path
    try:
        gate = gates.load_gate_section(config_path, "prd_review")
    except ValueError:
        gate = {}

    ticket = args.ticket.strip()
    slug_hint = args.slug_hint.strip() or None

    enabled = bool(gate.get("enabled", True))
    if not enabled:
        return 0

    if gates.matches(gate.get("skip_branches"), args.branch):
        return 0
    branches = gate.get("branches")
    if branches and not gates.matches(branches, args.branch):
        return 0

    code_prefixes = tuple(_normalize_items(gate.get("code_prefixes"), suffix="/") or DEFAULT_CODE_PREFIXES)
    code_globs = tuple(_normalize_items(gate.get("code_globs")))
    normalized = _normalize_file_path(args.file_path, root)
    target_suffix = f"docs/prd/{ticket}.prd.md"
    if args.skip_on_prd_edit and normalized.endswith(target_suffix):
        return 0
    if normalized and not _is_code_path(normalized, code_prefixes, code_globs):
        return 0

    prd_path = root / "docs" / "prd" / f"{ticket}.prd.md"
    if not prd_path.is_file():
        expected = prd_path.as_posix()
        print(
            f"BLOCK: missing PRD (expected {expected}) -> open aidd/docs/prd/{ticket}.prd.md, complete the dialog, and finish /feature-dev-aidd:review-spec {feature_label(ticket, slug_hint) or ticket}."
        )
        return 1

    allow_missing = bool(gate.get("allow_missing_section", False))
    require_closed = bool(gate.get("require_action_items_closed", True))
    approved: set[str] = {str(item).lower() for item in gate.get("approved_statuses", DEFAULT_APPROVED)}
    blocking: set[str] = {str(item).lower() for item in gate.get("blocking_statuses", DEFAULT_BLOCKING)}

    content = prd_path.read_text(encoding="utf-8")
    dialog_status = extract_dialog_status(content)
    if dialog_status == "draft":
        print(format_message("draft_dialog", ticket, slug_hint))
        return 1
    found, status, action_items = parse_review_section(content)

    if not found:
        if allow_missing:
            return 0
        print(format_message("missing_section", ticket, slug_hint))
        return 1

    if status in blocking:
        print(format_message("blocking_status", ticket, slug_hint, status))
        return 1

    if approved and status not in approved:
        print(format_message("not_approved", ticket, slug_hint, status))
        return 1

    if require_closed:
        for item in action_items:
            if item.startswith("- [ ]"):
                print(format_message("open_actions", ticket, slug_hint, status))
                return 1

    allow_missing_report = bool(gate.get("allow_missing_report", False))
    report_template = gate.get("report_path") or "aidd/reports/prd/{ticket}.json"
    resolved_report = report_template.replace("{ticket}", ticket).replace("{slug}", slug_hint or ticket)
    report_path = _resolve_report_path(root, resolved_report)

    report_data = None
    if report_path.exists():
        try:
            report_data = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            print(format_message("report_corrupted", ticket, slug_hint))
            return 1
    else:
        if report_path.suffix == ".json":
            candidate = report_path.with_suffix(".pack.json")
            if candidate.exists():
                try:
                    report_data = json.loads(candidate.read_text(encoding="utf-8"))
                except Exception:
                    print(format_message("report_corrupted", ticket, slug_hint))
                    return 1

    report_status = ""
    if report_data is not None:
        if isinstance(report_data, dict):
            report_status = str(report_data.get("status") or "").strip().lower()
            if not report_status:
                report_status = str(report_data.get("recommended_status") or "").strip().lower()
        if report_status and status and report_status != status:
            print(format_message("status_mismatch", ticket, slug_hint, status, report_status))
            return 1

    if report_data is not None:
        raw_findings = report_data.get("findings") or []
        findings = _inflate_columnar(raw_findings) if isinstance(raw_findings, dict) else raw_findings
        blocking_severities: set[str] = {
            str(item).lower() for item in gate.get("blocking_severities", DEFAULT_BLOCKING_SEVERITIES)
        }
        if blocking_severities:
            for finding in findings:
                severity = ""
                if isinstance(finding, dict):
                    severity = str(finding.get("severity") or "").lower()
                if severity and severity in blocking_severities:
                    label = feature_label(ticket, slug_hint)
                    print(
                        f"BLOCK: PRD Review contains '{severity}' findings -> update PRD and rerun /feature-dev-aidd:review-spec {label or ticket}."
                    )
                    return 1
    elif not allow_missing_report:
        if "{ticket}" in report_template or "{slug}" in report_template:
            message = format_message("missing_report", ticket, slug_hint)
        else:
            label = feature_label(ticket, slug_hint)
            message = f"BLOCK: missing PRD Review report ({report_path}) -> rerun /feature-dev-aidd:review-spec {label or ticket}"
        print(message)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(run_gate(parse_args()))
