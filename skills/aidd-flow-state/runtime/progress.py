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
import dataclasses
import fnmatch
import json
import os
import re
import subprocess
from collections.abc import Sequence
from pathlib import Path

from aidd_runtime import gates, runtime
from aidd_runtime.feature_ids import resolve_identifiers

DEFAULT_CODE_PREFIXES: tuple[str, ...] = (
    "src/",
    "tests/",
    "test/",
    "app/",
    "apps/",
    "service/",
    "services/",
    "backend/",
    "frontend/",
    "lib/",
    "libs/",
    "core/",
    "packages/",
    "modules/",
    "cmd/",
)
DEFAULT_CODE_SUFFIXES = {
    ".py",
    ".pyi",
    ".kt",
    ".kts",
    ".java",
    ".groovy",
    ".gradle",
    ".go",
    ".rs",
    ".swift",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
    ".hh",
    ".rb",
    ".php",
    ".scala",
    ".sql",
    ".cs",
    ".fs",
    ".dart",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
}
DEFAULT_OVERRIDE_ENV = "AIDD_SKIP_TASKLIST_PROGRESS"
DEFAULT_SOURCES: tuple[str, ...] = ()
TASKLIST_DIR = Path("docs") / "tasklist"
PROGRESS_LOG_MAX_LINES = 20
PROGRESS_LOG_MAX_LEN = 240
PROGRESS_LOG_SOURCES = {"implement", "review", "qa", "research", "normalize"}
PROGRESS_LOG_KINDS = {"iteration", "handoff"}
PROGRESS_LOG_RE = re.compile(
    r"^\s*-\s*(?P<date>\d{4}-\d{2}-\d{2})\s+"
    r"source=(?P<source>[A-Za-z0-9_-]+)\s+"
    r"id=(?P<item_id>[A-Za-z0-9_.:-]+)\s+"
    r"kind=(?P<kind>[A-Za-z0-9_-]+)\s+"
    r"hash=(?P<hash>[A-Za-z0-9]+)"
    r"(?:\s+link=(?P<link>\S+))?\s+"
    r"msg=(?P<msg>.+)$"
)


def _normalize_prefix(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    if not normalized:
        return normalized
    if not normalized.endswith("/"):
        normalized = f"{normalized}/"
    return normalized


def _normalize_pattern(value: str) -> str:
    return value.strip().replace("\\", "/")


def _is_truthy(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on", "enabled"}


@dataclasses.dataclass(frozen=True)
class ProgressConfig:
    enabled: bool
    code_prefixes: tuple[str, ...]
    code_globs: tuple[str, ...]
    skip_branches: tuple[str, ...]
    allow_missing_tasklist: bool
    override_env: str | None
    sources: tuple[str, ...]

    @classmethod
    def load(cls, root: Path) -> ProgressConfig:
        try:
            data = gates.load_gates_config(root)
        except ValueError:
            data = {}

        section = data.get("tasklist_progress")
        if not section:
            return cls(
                enabled=False,
                code_prefixes=DEFAULT_CODE_PREFIXES,
                code_globs=(),
                skip_branches=(),
                allow_missing_tasklist=False,
                override_env=None,
                sources=DEFAULT_SOURCES,
            )

        prefixes_raw = section.get("code_prefixes", DEFAULT_CODE_PREFIXES)
        prefixes: list[str] = []
        for value in prefixes_raw:
            try:
                normalized = _normalize_prefix(str(value))
            except Exception:
                continue
            if normalized:
                prefixes.append(normalized)
        if not prefixes:
            prefixes = list(DEFAULT_CODE_PREFIXES)

        globs_raw = section.get("code_globs", ())
        globs: list[str] = []
        for value in globs_raw:
            try:
                normalized = _normalize_pattern(str(value))
            except Exception:
                continue
            if normalized:
                globs.append(normalized)

        skip_branches = tuple(gates.normalize_patterns(section.get("skip_branches")) or ())

        sources_raw = section.get("sources", DEFAULT_SOURCES)
        sources = tuple(str(value).strip().lower() for value in sources_raw if str(value).strip())

        override_env = section.get("override_env")
        if override_env is not None:
            override_env = str(override_env).strip() or None

        return cls(
            enabled=bool(section.get("enabled", True)),
            code_prefixes=tuple(prefixes),
            code_globs=tuple(globs),
            skip_branches=skip_branches,
            allow_missing_tasklist=bool(section.get("allow_missing_tasklist", False)),
            override_env=override_env,
            sources=sources,
        )


@dataclasses.dataclass
class ProgressCheckResult:
    status: str
    ticket: str | None
    slug_hint: str | None
    tasklist_path: Path | None
    code_files: list[str]
    new_items: list[str]
    message: str

    def exit_code(self) -> int:
        return 0 if not self.status.startswith("error:") else 1

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "ticket": self.ticket,
            "slug_hint": self.slug_hint,
            "tasklist": str(self.tasklist_path) if self.tasklist_path else None,
            "code_files": list(self.code_files),
            "new_items": list(self.new_items),
            "message": self.message,
        }


def _is_git_repository(root: Path) -> bool:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return False
    if proc.returncode != 0:
        return False
    return proc.stdout.strip().lower() == "true"


def _run_git(root: Path, args: Sequence[str]) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return []
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _git_toplevel(root: Path) -> Path | None:
    lines = _run_git(root, ["rev-parse", "--show-toplevel"])
    if not lines:
        return None
    return Path(lines[0]).expanduser().resolve()


def _collect_changed_files(root: Path) -> tuple[list[str], bool]:
    if not _is_git_repository(root):
        return ([], False)
    candidates: list[str] = []
    for args in (
        ["diff", "--name-only"],
        ["diff", "--name-only", "--cached"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        candidates.extend(_run_git(root, args))

    ordered: list[str] = []
    seen: set[str] = set()
    for value in candidates:
        normalized = value.replace("\\", "/")
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered, True


def _read_git_file(root: Path, relative: Path) -> str:
    rel = str(relative).replace("\\", "/")
    repo_root = _git_toplevel(root)
    if repo_root is not None:
        try:
            target = (root / relative).resolve()
        except OSError:
            target = root / relative
        try:
            rel = str(target.relative_to(repo_root)).replace("\\", "/")
        except ValueError:
            rel = str(relative).replace("\\", "/")
    try:
        proc = subprocess.run(
            ["git", "show", f"HEAD:{rel}"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout




def _is_code_file(path: str, config: ProgressConfig) -> bool:
    normalized = path.replace("\\", "/")
    if normalized.startswith(str(TASKLIST_DIR)):
        return False
    for prefix in config.code_prefixes:
        if normalized.startswith(prefix):
            return True
    for pattern in config.code_globs:
        if fnmatch.fnmatch(normalized, pattern):
            return True
    suffix = Path(normalized).suffix.lower()
    if suffix in DEFAULT_CODE_SUFFIXES and not normalized.startswith("docs/"):
        return True
    return False


def _summarise_paths(paths: Sequence[str], limit: int = 3) -> str:
    if not paths:
        return ""
    if len(paths) <= limit:
        return ", ".join(paths)
    remaining = len(paths) - limit
    return ", ".join(paths[:limit]) + f", … (+{remaining})"


def _format_list(items: Sequence[str], prefix: str = "- ", limit: int = 5) -> str:
    if not items:
        return ""
    lines: list[str] = []
    for index, item in enumerate(items):
        if index == limit:
            lines.append(f"{prefix}… (+{len(items) - limit})")
            break
        lines.append(f"{prefix}{item}")
    return "\n".join(lines)


def parse_progress_log_lines(lines: Sequence[str]) -> tuple[list[dict], list[str]]:
    entries: list[dict] = []
    invalid: list[str] = []
    for raw in lines:
        if not raw.strip().startswith("-"):
            continue
        stripped = raw.strip().lower()
        if stripped.startswith("- (empty)") or stripped.startswith("- ..."):
            continue
        match = PROGRESS_LOG_RE.match(raw)
        if not match:
            invalid.append(raw)
            continue
        info = match.groupdict()
        info["source"] = info["source"].lower()
        info["kind"] = info["kind"].lower()
        info["msg"] = info["msg"].strip()
        entries.append(info)
    return entries, invalid


def dedupe_progress_log(entries: Sequence[dict]) -> list[dict]:
    seen = set()
    deduped: list[dict] = []
    for entry in entries:
        key = (entry.get("date"), entry.get("source"), entry.get("item_id"), entry.get("hash"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    return deduped


def format_progress_log_entry(entry: dict) -> str:
    parts = [
        f"- {entry['date']}",
        f"source={entry['source']}",
        f"id={entry['item_id']}",
        f"kind={entry['kind']}",
        f"hash={entry['hash']}",
    ]
    if entry.get("link"):
        parts.append(f"link={entry['link']}")
    msg = entry.get("msg") or ""
    if len(msg) > 200:
        msg = msg[:197] + "..."
    parts.append(f"msg={msg}")
    line = " ".join(parts)
    if len(line) > PROGRESS_LOG_MAX_LEN:
        line = line[: PROGRESS_LOG_MAX_LEN - 3] + "..."
    return line


def normalize_progress_log(
    lines: Sequence[str],
    *,
    max_lines: int = PROGRESS_LOG_MAX_LINES,
) -> tuple[list[str], list[str], list[str]]:
    entries, invalid = parse_progress_log_lines(lines)
    deduped = dedupe_progress_log(entries)
    overflow: list[dict] = []
    if len(deduped) > max_lines:
        overflow = deduped[:-max_lines]
        deduped = deduped[-max_lines:]
    normalized = [format_progress_log_entry(entry) for entry in deduped]
    archived = [format_progress_log_entry(entry) for entry in overflow]
    summary: list[str] = []
    if invalid:
        summary.append(f"invalid={len(invalid)}")
    if overflow:
        summary.append(f"archived={len(overflow)}")
    return normalized, archived, summary


def _normalize_checkbox_line(line: str) -> str:
    normalized = " ".join(line.strip().split())
    return normalized.lower().replace("[x]", "[x]")


def _ordered_task_lines(content: str, *, checked: bool) -> list[tuple[str, str]]:
    marker = "- [x]" if checked else "- [ ]"
    result: list[tuple[str, str]] = []
    seen: set[str] = set()
    for raw in content.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if not stripped.lower().startswith(marker):
            continue
        normalized = _normalize_checkbox_line(stripped) if checked else " ".join(stripped.split()).lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append((normalized, stripped))
    return result


def _ordered_checked_lines(content: str) -> list[tuple[str, str]]:
    return _ordered_task_lines(content, checked=True)


def _ordered_open_lines(content: str) -> list[tuple[str, str]]:
    return _ordered_task_lines(content, checked=False)


def _diff_checked(old_text: str, new_text: str) -> list[str]:
    old_map = dict(_ordered_checked_lines(old_text))
    additions: list[str] = []
    for key, original in _ordered_checked_lines(new_text):
        if key not in old_map:
            additions.append(original)
    return additions


def _diff_open_tasks(old_text: str, new_text: str, *, require_reference: bool = False) -> list[str]:
    old_map = dict(_ordered_open_lines(old_text))
    additions: list[str] = []
    for key, original in _ordered_open_lines(new_text):
        if key in old_map:
            continue
        if require_reference and "reports/" not in original:
            continue
        additions.append(original)
    return additions


def check_progress(
    root: Path,
    ticket: str | None,
    *,
    slug_hint: str | None = None,
    source: str = "manual",
    branch: str | None = None,
    config: ProgressConfig | None = None,
) -> ProgressCheckResult:
    root = root.resolve()
    config = config or ProgressConfig.load(root)
    context = (source or "manual").lower()
    identifiers = resolve_identifiers(root, ticket=ticket, slug_hint=slug_hint)
    ticket = identifiers.resolved_ticket
    slug_hint = identifiers.slug_hint

    if not config.enabled:
        return ProgressCheckResult(
            status="skip:disabled",
            ticket=ticket,
            slug_hint=slug_hint,
            tasklist_path=None,
            code_files=[],
            new_items=[],
            message="Progress check is disabled (tasklist_progress.enabled=false).",
        )

    if config.override_env:
        override_raw = os.getenv(config.override_env, "")
        if override_raw and _is_truthy(override_raw.strip()):
            return ProgressCheckResult(
                status="skip:override",
                ticket=ticket,
                slug_hint=slug_hint,
                tasklist_path=None,
                code_files=[],
                new_items=[],
                message=f"Progress check skipped: {config.override_env}={override_raw.strip()}",
            )

    if config.sources and context not in config.sources:
        return ProgressCheckResult(
            status="skip:source",
            ticket=ticket,
            slug_hint=slug_hint,
            tasklist_path=None,
            code_files=[],
            new_items=[],
            message=f"Context `{context}` is not included in tasklist_progress.sources.",
        )

    detected_branch = branch or runtime.detect_branch(root)
    if detected_branch and config.skip_branches and gates.matches(config.skip_branches, detected_branch):
        return ProgressCheckResult(
            status="skip:branch",
            ticket=ticket,
            slug_hint=slug_hint,
            tasklist_path=None,
            code_files=[],
            new_items=[],
            message=f"Branch `{detected_branch}` is excluded by skip_branches.",
        )

    changed_files, git_available = _collect_changed_files(root)
    if not git_available:
        return ProgressCheckResult(
            status="skip:no-git",
            ticket=ticket,
            slug_hint=slug_hint,
            tasklist_path=None,
            code_files=[],
            new_items=[],
            message="Git repository not detected - progress check skipped.",
        )

    code_files = [path for path in changed_files if _is_code_file(path, config)]
    if not code_files:
        return ProgressCheckResult(
            status="skip:no-changes",
            ticket=ticket,
            slug_hint=slug_hint,
            tasklist_path=None,
            code_files=[],
            new_items=[],
            message="No code changes detected - no new checkboxes required.",
        )

    if not ticket:
        return ProgressCheckResult(
            status="error:no-ticket",
            ticket=None,
            slug_hint=slug_hint,
            tasklist_path=None,
            code_files=code_files,
            new_items=[],
            message="Failed to determine feature ticket. Ensure docs/.active.json is populated or pass --ticket.",
        )

    tasklist_rel = TASKLIST_DIR / f"{ticket}.md"
    tasklist_path = root / tasklist_rel
    if not tasklist_path.exists():
        if config.allow_missing_tasklist:
            return ProgressCheckResult(
                status="skip:missing-tasklist",
                ticket=ticket,
                slug_hint=slug_hint,
                tasklist_path=tasklist_path,
                code_files=code_files,
                new_items=[],
                message=f"{tasklist_rel} is missing, but allow_missing_tasklist=true - check skipped.",
            )
        return ProgressCheckResult(
            status="error:no-tasklist",
            ticket=ticket,
            slug_hint=slug_hint,
            tasklist_path=tasklist_path,
            code_files=code_files,
            new_items=[],
            message=f"BLOCK: {tasklist_rel} not found. Create it with `/feature-dev-aidd:tasks-new {ticket}` and record progress.",
        )

    try:
        new_text = tasklist_path.read_text(encoding="utf-8")
    except OSError as exc:
        return ProgressCheckResult(
            status="error:read-tasklist",
            ticket=ticket,
            slug_hint=slug_hint,
            tasklist_path=tasklist_path,
            code_files=code_files,
            new_items=[],
            message=f"Failed to read {tasklist_rel}: {exc}.",
        )

    old_text = _read_git_file(root, tasklist_rel)
    new_items = _diff_checked(old_text, new_text)
    if new_items:
        return ProgressCheckResult(
            status="ok",
            ticket=ticket,
            slug_hint=slug_hint,
            tasklist_path=tasklist_path,
            code_files=code_files,
            new_items=new_items,
            message="",
        )

    if context == "handoff":
        open_items = _diff_open_tasks(old_text, new_text, require_reference=True)
        if open_items:
            return ProgressCheckResult(
                status="ok",
                ticket=ticket,
                slug_hint=slug_hint,
                tasklist_path=tasklist_path,
                code_files=code_files,
                new_items=open_items,
                message="",
            )

    summary = _summarise_paths(code_files)
    if context == "handoff":
        guidance = (
            f"BLOCK: feature `{ticket}` has code changes ({summary}), "
            f"but handoff tasks were not added. Add new `- [ ] ... (source: aidd/reports/qa|research/...)` "
            f"to {tasklist_rel} and rerun `python3 ${{AIDD_ROOT}}/skills/aidd-flow-state/runtime/progress_cli.py "
            f"--source handoff --ticket {ticket}`."
        )
    else:
        guidance = (
            f"BLOCK: feature `{ticket}` has code changes ({summary}), "
            f"but file {tasklist_rel} has no new `- [x]` entries.\n"
            "Move relevant items from `- [ ]` to `- [x]`, add date/iteration notes, "
            "update `Checkbox updated: ...`, and rerun `python3 ${AIDD_ROOT}/skills/aidd-flow-state/runtime/progress_cli.py "
            f"--source {context or 'manual'} --ticket {ticket}`."
        )
    return ProgressCheckResult(
        status="error:no-checkbox",
        ticket=ticket,
        slug_hint=slug_hint,
        tasklist_path=tasklist_path,
        code_files=code_files,
        new_items=[],
        message=guidance,
    )


def _build_success_message(result: ProgressCheckResult) -> str:
    if result.status == "ok":
        lines = ["Tasklist progress confirmed."]
        if result.new_items:
            lines.append("New checkboxes:")
            lines.append(_format_list(result.new_items, prefix="  - "))
        return "\n".join(lines)
    if result.status.startswith("skip:"):
        return result.message
    return ""


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that tasklist has new `- [x]` items after code changes."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project directory (default: current directory).",
    )
    parser.add_argument(
        "--ticket",
        "--slug",
        dest="ticket",
        help="Feature ticket identifier. Defaults to docs/.active.json.",
    )
    parser.add_argument(
        "--slug-hint",
        dest="slug_hint",
        help="Optional slug hint (defaults to docs/.active.json when present).",
    )
    parser.add_argument(
        "--branch",
        help="Branch name for skip_branches evaluation (default: autodetect).",
    )
    parser.add_argument(
        "--source",
        choices=("manual", "implement", "qa", "review", "gate", "handoff"),
        default="manual",
        help="Call context affecting messages and skip rules.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Return result in JSON format.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed information even on success.",
    )
    parser.add_argument(
        "--quiet-ok",
        action="store_true",
        help="Suppress output for OK/skip status (except JSON).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    root = Path(args.root).resolve()
    identifiers = resolve_identifiers(root, ticket=args.ticket, slug_hint=args.slug_hint)
    ticket = identifiers.resolved_ticket
    slug_hint = identifiers.slug_hint
    branch = args.branch or runtime.detect_branch(root)
    config = ProgressConfig.load(root)

    result = check_progress(
        root=root,
        ticket=ticket,
        slug_hint=slug_hint,
        source=args.source,
        branch=branch,
        config=config,
    )

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return result.exit_code()

    should_print = True
    if result.exit_code() == 0 and args.quiet_ok and not args.verbose:
        should_print = False

    if should_print:
        if result.message:
            print(result.message)
        elif args.verbose:
            success_msg = _build_success_message(result)
            if success_msg:
                print(success_msg)
        elif result.exit_code() != 0:
            print("BLOCK: progress check failed.")

        if args.verbose:
            if result.code_files:
                print("Changed files:")
                print(_format_list(result.code_files))
            if result.new_items and result.status == "ok":
                print("New checkboxes:")
                print(_format_list(result.new_items))

    return result.exit_code()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
