#!/usr/bin/env python3
"""Heuristic QA agent used by gate-qa.sh and CI workflows.

The agent analyses the current workspace (or diff against a base commit),
collects lightweight QA findings and produces a structured report with
severity levels. In gate mode it prints a short summary and returns a non-zero
exit code when blocking issues are detected.
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
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from aidd_runtime import runtime
from aidd_runtime.feature_ids import resolve_aidd_root, resolve_identifiers


def detect_project_root(target: Path | None = None) -> Path:
    return resolve_aidd_root(target or Path.cwd())


ROOT_DIR = Path.cwd()

DEFAULT_BLOCKERS = ("blocker", "critical")
DEFAULT_WARNINGS = ("major", "minor")
SEVERITY_ORDER = ["blocker", "critical", "major", "minor", "info"]
MANUAL_MARKERS = ("manual",)


def _normalize_id_text(value: str) -> str:
    return " ".join(str(value).strip().split())


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha1()
    digest.update(prefix.encode("utf-8"))
    digest.update(b"|")
    for part in parts:
        digest.update(_normalize_id_text(str(part)).encode("utf-8"))
        digest.update(b"|")
    return digest.hexdigest()[:12]


def feature_label(ticket: str | None, slug_hint: str | None) -> str:
    ticket_value = (ticket or "").strip()
    hint_value = (slug_hint or "").strip()
    if not ticket_value:
        return ""
    if hint_value and hint_value != ticket_value:
        return f"{ticket_value} (slug hint: {hint_value})"
    return ticket_value


@dataclass
class Finding:
    severity: str
    scope: str
    title: str
    details: str
    recommendation: str
    id: str = ""
    blocking: bool = False

    def __post_init__(self) -> None:
        if not self.id:
            self.id = _stable_id(
                "qa",
                self.scope,
                self.title,
            )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "severity": self.severity,
            "scope": self.scope,
            "blocking": self.blocking,
            "title": self.title,
            "details": self.details,
            "recommendation": self.recommendation,
        }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run heuristic QA checks for the current Claude workflow project."
    )
    parser.add_argument("--ticket", "--slug", dest="ticket", help="Active feature ticket (alias: --slug).")
    parser.add_argument("--slug-hint", dest="slug_hint", help="Optional slug hint used for messaging.")
    parser.add_argument("--branch", help="Current branch name. Autodetected when omitted.")
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format for the generated report (default: json).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional path to write JSON report. Directories are created automatically.",
    )
    parser.add_argument(
        "--gate",
        action="store_true",
        help="Enable gate mode: print human-readable summary and exit with non-zero code on blockers.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not fail the process even if blockers are detected (gate mode only).",
    )
    parser.add_argument(
        "--block-on",
        default=",".join(DEFAULT_BLOCKERS),
        help="Comma separated list of severities treated as blockers.",
    )
    parser.add_argument(
        "--warn-on",
        default=",".join(DEFAULT_WARNINGS),
        help="Comma separated list of severities treated as warnings (non-blocking).",
    )
    parser.add_argument(
        "--emit-json",
        action="store_true",
        help="Emit JSON to stdout even in gate mode (useful for tooling).",
    )
    parser.add_argument(
        "--emit-patch",
        action="store_true",
        help="Emit RFC6902 patch file when a previous report exists.",
    )
    parser.add_argument(
        "--pack-only",
        action="store_true",
        help="Remove JSON report after writing pack sidecar.",
    )
    parser.add_argument(
        "--scope",
        action="append",
        help="Optional scope filters (reserved for future heuristics).",
    )
    return parser.parse_args(argv)


def detect_feature(ticket_arg: str | None, slug_hint_arg: str | None) -> tuple[str | None, str | None]:
    identifiers = resolve_identifiers(ROOT_DIR, ticket=ticket_arg, slug_hint=slug_hint_arg)
    return identifiers.resolved_ticket, identifiers.slug_hint


def run_git(args: Sequence[str]) -> list[str]:
    cmd = ["git", *args]
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT_DIR,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return []
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def collect_changed_files() -> list[str]:
    files: set[str] = set()
    diff_base = os.environ.get("QA_AGENT_DIFF_BASE", "").strip()
    if diff_base:
        files.update(run_git(["diff", "--name-only", f"{diff_base}...HEAD"]))
    files.update(run_git(["diff", "--name-only", "HEAD"]))
    files.update(run_git(["diff", "--name-only", "--cached"]))
    files.update(run_git(["ls-files", "--others", "--exclude-standard"]))
    return sorted(files)


def _find_token_lines(content: str, token: str) -> Iterable[tuple[int, str]]:
    for idx, line in enumerate(content.splitlines(), start=1):
        if token in line:
            yield idx, line.strip()


def analyse_code_tokens(files: Iterable[str]) -> list[Finding]:
    findings: list[Finding] = []
    token_rules = {
        "FIXME": (
            "blocker",
            "Found FIXME in code",
            "Remove or resolve FIXME before merge (QA blocker).",
        ),
        "TODO": (
            "major",
            "Unresolved TODO",
            "Resolve TODO or move it into a tracked task before release.",
        ),
    }
    for relative in files:
        path = ROOT_DIR / relative
        if not path.is_file():
            continue
        # Limit scanning to source files and tests.
        if not any(part in relative for part in ("src/", "tests/", ".kt", ".java", ".py", ".js", ".ts", ".tsx", ".json", ".yaml")):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for token, (severity, title, recommendation) in token_rules.items():
            matches = list(_find_token_lines(content, token))
            if not matches:
                continue
            line_no, snippet = matches[0]
            findings.append(
                Finding(
                    severity=severity,
                    scope=relative,
                    title=title,
                    details=f"{relative}:{line_no} → {snippet}",
                    recommendation=recommendation,
                )
            )
    return findings


def _is_heading(line: str) -> bool:
    return bool(re.match(r"^#{1,6}\s+", line))


def _is_qa_checklist_heading(line: str) -> bool:
    return "AIDD:CHECKLIST_QA" in line


def _extract_blocking_flag(line: str) -> bool | None:
    match = re.search(r"\(Blocking:\s*(true|false)\)", line, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).lower() == "true"


def analyse_tasklist(ticket: str | None, slug_hint: str | None) -> tuple[list[Finding], list[str]]:
    tasklist_dir = ROOT_DIR / "docs" / "tasklist"
    candidates: list[Path] = []
    if ticket:
        candidate = tasklist_dir / f"{ticket}.md"
        if candidate.exists():
            candidates.append(candidate)
    else:
        candidates.extend(sorted(tasklist_dir.glob("*.md")))
    findings: list[Finding] = []
    manual_required: list[str] = []
    for tasklist_path in candidates:
        try:
            lines = tasklist_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        in_front_matter = False
        in_qa_checklist = False
        in_handoff_qa = False
        for idx, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if stripped == "---":
                in_front_matter = not in_front_matter
                continue
            if in_front_matter:
                continue
            if stripped == "<!-- handoff:qa start -->":
                in_handoff_qa = True
                continue
            if stripped == "<!-- handoff:qa end -->":
                in_handoff_qa = False
                continue
            if _is_heading(stripped):
                if _is_qa_checklist_heading(stripped):
                    in_qa_checklist = True
                else:
                    in_qa_checklist = False
                continue
            if not stripped.startswith("- ["):
                continue
            if re.match(r"- \[[xX]\]", stripped):
                continue
            if in_qa_checklist:
                is_manual = any(marker in stripped.lower() for marker in MANUAL_MARKERS)
                if is_manual:
                    manual_required.append(f"{tasklist_path.relative_to(ROOT_DIR)}:{idx} → {stripped}")
                rel_path = tasklist_path.relative_to(ROOT_DIR)
                checklist_id = _stable_id("qa-checklist", str(rel_path), stripped)
                findings.append(
                    Finding(
                        severity="major" if is_manual else "blocker",
                        scope="checklist",
                        title=f"Open QA item in {tasklist_path.relative_to(ROOT_DIR)}",
                        details=f"{tasklist_path.relative_to(ROOT_DIR)}:{idx} → {stripped}",
                        recommendation="Close QA checklist items or move them to backlog with rationale.",
                        id=checklist_id,
                    )
                )
                continue
            if not in_handoff_qa:
                continue
            blocking_flag = _extract_blocking_flag(stripped)
            if blocking_flag is None:
                continue
            rel_path = tasklist_path.relative_to(ROOT_DIR)
            handoff_id = _stable_id("qa-handoff", str(rel_path), stripped)
            findings.append(
                Finding(
                    severity="blocker" if blocking_flag else "major",
                    scope="checklist",
                    title=f"Open QA item in {tasklist_path.relative_to(ROOT_DIR)}",
                    details=f"{tasklist_path.relative_to(ROOT_DIR)}:{idx} → {stripped}",
                    recommendation="Close QA checklist items or move them to backlog with rationale.",
                    id=handoff_id,
                    blocking=blocking_flag,
                )
            )
    return findings, manual_required


def analyse_tests_coverage(files: Sequence[str]) -> list[Finding]:
    main_changes = [f for f in files if f.startswith("src/main/")]
    test_changes = [f for f in files if f.startswith("src/test/") or f.startswith("tests/")]
    if not main_changes or test_changes:
        return []
    changed_preview = ", ".join(main_changes[:3])
    if len(main_changes) > 3:
        changed_preview += "…"
    return [
        Finding(
            severity="major",
            scope="tests",
            title="No test updates for changed code",
            details=f"Changed files ({len(main_changes)}): {changed_preview}",
            recommendation="Add or update tests, or document why extra coverage is not required.",
        )
    ]


def load_tests_metadata() -> tuple[str, list[dict], bool]:
    summary = (os.environ.get("QA_TESTS_SUMMARY") or "").strip().lower() or "not-run"
    allow_no_tests = (os.environ.get("QA_ALLOW_NO_TESTS") or "").strip() == "1"
    executed_raw = os.environ.get("QA_TESTS_EXECUTED") or ""
    executed: list[dict] = []
    if executed_raw:
        try:
            parsed = json.loads(executed_raw)
            if isinstance(parsed, list):
                executed = parsed
        except json.JSONDecodeError:
            executed = []
    return summary, executed, allow_no_tests


def analyse_tests_run(summary: str, executed: list[dict], allow_missing: bool) -> list[Finding]:
    findings: list[Finding] = []
    summary = summary.strip().lower() if summary else "not-run"
    if summary == "fail":
        log_hint = ""
        for entry in executed:
            if str(entry.get("status")).lower() == "fail":
                log_hint = entry.get("log") or entry.get("log_path") or ""
                break
        details = f"Log: {log_hint}" if log_hint else ""
        findings.append(
            Finding(
                severity="blocker",
                scope="tests",
                title="Automated tests failed",
                details=details,
                recommendation="Fix failing tests and rerun.",
            )
        )
    elif summary in {"not-run", "skipped"}:
        severity = "major" if allow_missing else "blocker"
        findings.append(
            Finding(
                severity=severity,
                scope="tests",
                title="Tests were not executed",
                details="Automated tests did not run in QA stage.",
                recommendation="Run automated tests or document the skip reason.",
            )
        )
    return findings


def aggregate_findings(
    files: Sequence[str],
    ticket: str | None,
    slug_hint: str | None,
    *,
    tests_summary: str,
    tests_executed: list[dict],
    allow_missing_tests: bool,
) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    findings.extend(analyse_code_tokens(files))
    tasklist_findings, manual_required = analyse_tasklist(ticket, slug_hint)
    findings.extend(tasklist_findings)
    findings.extend(analyse_tests_coverage(files))
    findings.extend(analyse_tests_run(tests_summary, tests_executed, allow_missing_tests))
    return findings, manual_required


def dedupe_findings(findings: Sequence[Finding]) -> list[Finding]:
    seen: set[str] = set()
    deduped: list[Finding] = []
    for finding in findings:
        if finding.id in seen:
            continue
        seen.add(finding.id)
        deduped.append(finding)
    return deduped


def summarise(
    findings: Sequence[Finding],
    *,
    blockers_set: set[str] | None = None,
    warnings_set: set[str] | None = None,
) -> tuple[str, dict, int, int, str]:
    counts = dict.fromkeys(SEVERITY_ORDER, 0)
    for finding in findings:
        severity = finding.severity.lower()
        counts[severity] = counts.get(severity, 0) + 1

    active_blockers = blockers_set or {"blocker", "critical"}
    active_warnings = warnings_set or {"major", "minor"}
    blockers = sum(counts.get(severity, 0) for severity in active_blockers)
    warnings = sum(counts.get(severity, 0) for severity in active_warnings)

    parts: list[str] = []
    if blockers:
        parts.append(f"blockers {blockers}")
    if warnings:
        parts.append(f"warnings {warnings}")
    if not parts:
        summary = "no findings"
    else:
        summary = ", ".join(parts)
    summary = f"Summary: {summary}."

    if blockers:
        status = "BLOCKED"
    elif warnings:
        status = "WARN"
    else:
        status = "READY"

    return summary, counts, blockers, warnings, status


def write_report(report_path: Path, payload: dict) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def dedupe_strings(items: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        key = item.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    global ROOT_DIR
    ROOT_DIR = detect_project_root()
    ticket, slug_hint = detect_feature(args.ticket, args.slug_hint)
    branch = args.branch or runtime.detect_branch(ROOT_DIR)
    files = collect_changed_files()
    tests_summary, tests_executed, allow_missing_tests = load_tests_metadata()
    findings, manual_required = aggregate_findings(
        files,
        ticket,
        slug_hint,
        tests_summary=tests_summary,
        tests_executed=tests_executed,
        allow_missing_tests=allow_missing_tests,
    )
    findings = dedupe_findings(findings)
    manual_required = dedupe_strings(manual_required)

    blockers_set = {sev.strip().lower() for sev in args.block_on.split(",") if sev.strip()}
    warnings_set = {sev.strip().lower() for sev in args.warn_on.split(",") if sev.strip()}

    for finding in findings:
        finding.blocking = finding.severity.lower() in blockers_set

    summary, counts, blockers, warnings, status = summarise(
        findings,
        blockers_set=blockers_set,
        warnings_set=warnings_set,
    )
    label = feature_label(ticket, slug_hint)
    generated_at = (
        dt.datetime.now(dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    )

    payload = {
        "generated_at": generated_at,
        "status": status,
        "summary": summary,
        "ticket": ticket,
        "slug_hint": slug_hint,
        "branch": branch,
        "counts": counts,
        "files_considered": files,
        "findings": [finding.to_dict() for finding in findings],
        "manual_required": manual_required,
        "tests_summary": tests_summary,
        "tests_executed": tests_executed,
        "inputs": {
            "diff_base": os.environ.get("QA_AGENT_DIFF_BASE") or None,
        },
    }

    if args.report:
        previous_payload = None
        if args.emit_patch and args.report.exists():
            try:
                previous_payload = json.loads(args.report.read_text(encoding="utf-8"))
            except Exception:
                previous_payload = None

        write_report(args.report, payload)
        pack_path = None
        try:
            from aidd_runtime import reports_pack

            pack_path = reports_pack.write_qa_pack(args.report, root=ROOT_DIR)
        except Exception as exc:
            print(f"[qa-agent] WARN: failed to generate pack: {exc}", file=sys.stderr)

        if args.emit_patch and previous_payload is not None:
            try:
                from aidd_runtime import json_patch as _json_patch

                patch_ops = _json_patch.diff(previous_payload, payload)
                patch_path = args.report.with_suffix(".patch.json")
                patch_path.write_text(
                    json.dumps(patch_ops, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            except Exception as exc:
                print(f"[qa-agent] WARN: failed to emit patch: {exc}", file=sys.stderr)

        pack_only = bool(args.pack_only or os.getenv("AIDD_PACK_ONLY", "").strip() == "1")
        if pack_only and pack_path and pack_path.exists():
            try:
                args.report.unlink()
            except OSError:
                pass

    if not args.gate or args.emit_json:
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(summary)

    if args.gate:
        log_prefix = "[qa-agent]"
        context = f"{label}" if label else ""
        if context:
            print(f"{log_prefix} {summary} (feature: {context})", file=sys.stderr)
        else:
            print(f"{log_prefix} {summary}", file=sys.stderr)
        for finding in findings:
            severity = finding.severity.upper()
            scope = finding.scope or "-"
            print(f"{log_prefix} {severity} [{scope}] {finding.title}", file=sys.stderr)
            if finding.details:
                print(f"{log_prefix}   {finding.details}", file=sys.stderr)
            if finding.recommendation:
                print(f"{log_prefix}   → {finding.recommendation}", file=sys.stderr)

        has_blockers = any(f.blocking for f in findings)
        if has_blockers and not args.dry_run:
            return 1
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
