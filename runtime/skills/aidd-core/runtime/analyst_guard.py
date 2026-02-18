from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from aidd_runtime import gates
from aidd_runtime.feature_ids import resolve_aidd_root

# Allow Markdown prefixes (headings/bullets/bold) so analyst output doesn't trip the gate.
QUESTION_RE = re.compile(
    r"^\s*(?:[#>*-]+\s*)?(?:\*\*)?Question\s+(\d+)\b[^:\n]*:(?:\*\*)?",
    re.MULTILINE,
)
ANSWER_RE = re.compile(
    r"^\s*(?:[#>*-]+\s*)?(?:\*\*)?Answer\s+(\d+)\b(?:\*\*)?\s*:",
    re.MULTILINE,
)
STATUS_RE = re.compile(r"^\s*Status:\s*([A-Za-z]+)", re.MULTILINE)
DIALOG_HEADING = "## Dialog analyst"
ANSWERS_HEADING = "## AIDD:ANSWERS"
OPEN_QUESTIONS_HEADING = "## 10. Open Questions"
AIDD_OPEN_QUESTIONS_HEADING = "## AIDD:OPEN_QUESTIONS"
Q_RE = re.compile(r"\bQ(\d+)\b")
NONE_VALUES = {"none", "n/a", "na"}
OPEN_ITEM_PREFIX_RE = re.compile(r"^(?:[-*+]\s+|\d+\.\s+)")
CHECKBOX_PREFIX_RE = re.compile(r"^\[[ xX]\]\s*")
ALLOWED_STATUSES = {"READY", "BLOCKED", "PENDING"}
RESEARCH_REF_TEMPLATE = "docs/research/{ticket}.md"


class AnalystValidationError(RuntimeError):
    """Raised when analyst dialog validation fails."""


@dataclass
class AnalystSettings:
    enabled: bool = True
    min_questions: int = 1
    require_ready: bool = True
    allow_blocked: bool = False
    check_open_questions: bool = True
    require_dialog_section: bool = True
    branches: list[str] | None = None
    skip_branches: list[str] | None = None


@dataclass
class AnalystCheckSummary:
    status: str | None
    question_count: int
    answered_count: int


def load_settings(root: Path) -> AnalystSettings:
    try:
        config = gates.load_gates_config(root)
    except ValueError as exc:  # pragma: no cover - defensive
        raise AnalystValidationError(str(exc))
    raw = config.get("analyst") or {}
    settings = AnalystSettings()

    if isinstance(raw, dict):
        if "enabled" in raw:
            settings.enabled = bool(raw["enabled"])
        if "min_questions" in raw:
            try:
                settings.min_questions = max(int(raw["min_questions"]), 0)
            except (ValueError, TypeError):
                raise AnalystValidationError("config/gates.json: analyst.min_questions must be a number")
        if "require_ready" in raw:
            settings.require_ready = bool(raw["require_ready"])
        if "allow_blocked" in raw:
            settings.allow_blocked = bool(raw["allow_blocked"])
        if "check_open_questions" in raw:
            settings.check_open_questions = bool(raw["check_open_questions"])
        if "require_dialog_section" in raw:
            settings.require_dialog_section = bool(raw["require_dialog_section"])
        settings.branches = gates.normalize_patterns(raw.get("branches"))
        settings.skip_branches = gates.normalize_patterns(raw.get("skip_branches"))

    return settings


def _extract_section(text: str, heading_prefix: str) -> str | None:
    lines = text.splitlines()
    start_idx: int | None = None
    heading_lower = heading_prefix.strip().lower()
    for idx, raw in enumerate(lines):
        if raw.strip().lower().startswith(heading_lower):
            start_idx = idx + 1
            break
    if start_idx is None:
        return None
    end_idx = len(lines)
    for idx in range(start_idx, len(lines)):
        if lines[idx].startswith("## ") and idx != start_idx:
            end_idx = idx
            break
    return "\n".join(lines[start_idx:end_idx]).strip()


def _collect_numbers(pattern: re.Pattern[str], text: str) -> list[int]:
    numbers: list[int] = []
    seen = set()
    for match in pattern.finditer(text):
        try:
            num = int(match.group(1))
        except ValueError:
            continue
        numbers.append(num)
        seen.add(num)
    return numbers


def _has_open_items(section: str) -> bool:
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(">"):
            continue
        normalized = OPEN_ITEM_PREFIX_RE.sub("", stripped)
        normalized = CHECKBOX_PREFIX_RE.sub("", normalized).strip()
        if normalized.startswith("`") and normalized.endswith("`") and len(normalized) > 1:
            normalized = normalized[1:-1].strip()
        if normalized.startswith("**") and normalized.endswith("**") and len(normalized) > 3:
            normalized = normalized[2:-2].strip()
        if normalized.startswith("__") and normalized.endswith("__") and len(normalized) > 3:
            normalized = normalized[2:-2].strip()
        if normalized.lower() in NONE_VALUES:
            continue
        return True
    return False


def _collect_q_numbers(section: str) -> set[int]:
    numbers: set[int] = set()
    for line in section.splitlines():
        for match in Q_RE.finditer(line):
            try:
                numbers.add(int(match.group(1)))
            except ValueError:
                continue
    return numbers


def validate_prd(
    root: Path,
    ticket: str,
    *,
    settings: AnalystSettings,
    branch: str | None = None,
    require_ready_override: bool | None = None,
    allow_blocked_override: bool | None = None,
    min_questions_override: int | None = None,
) -> AnalystCheckSummary:
    if not settings.enabled or not gates.branch_enabled(branch, allow=settings.branches, skip=settings.skip_branches):
        return AnalystCheckSummary(status=None, question_count=0, answered_count=0)

    prd_path = root / "docs" / "prd" / f"{ticket}.prd.md"
    if not prd_path.exists():
        raise AnalystValidationError(f"BLOCK: missing PRD -> run /feature-dev-aidd:idea-new {ticket}")

    text = prd_path.read_text(encoding="utf-8")
    dialog_section = _extract_section(text, DIALOG_HEADING)
    questions_source = dialog_section or text
    answers_section = _extract_section(text, ANSWERS_HEADING)
    answers_source = answers_section if answers_section is not None else (dialog_section or text)
    questions = _collect_numbers(QUESTION_RE, questions_source)
    answers = _collect_numbers(ANSWER_RE, answers_source)

    min_questions = settings.min_questions
    if min_questions_override is not None:
        min_questions = max(min_questions_override, 0)

    if settings.require_dialog_section and dialog_section is None:
        raise AnalystValidationError(
            f"BLOCK: PRD does not contain section `{DIALOG_HEADING}` -> rerun /feature-dev-aidd:idea-new with clarifications."
        )

    if min_questions and len(set(questions)) < min_questions:
        raise AnalystValidationError(
            f"BLOCK: analyst must ask at least {min_questions} question(s) in 'Question N: ...' format."
        )

    if questions:
        sorted_unique = sorted(set(questions))
        expected = list(range(1, sorted_unique[-1] + 1))
        if sorted_unique != expected:
            missing = [str(num) for num in expected if num not in sorted_unique]
            missing_repr = ", ".join(missing[:3])
            if len(missing) > 3:
                missing_repr += ", …"
            raise AnalystValidationError(
                f"BLOCK: question numbering sequence is broken (missing {missing_repr}). Renumber questions and answers."
            )

    status_match = STATUS_RE.search(text)
    status = status_match.group(1).upper() if status_match else None
    open_section = _extract_section(text, OPEN_QUESTIONS_HEADING)
    aidd_open_section = _extract_section(text, AIDD_OPEN_QUESTIONS_HEADING)
    if settings.check_open_questions and aidd_open_section:
        q_numbers = _collect_q_numbers(aidd_open_section)
        if q_numbers:
            question_numbers = set(questions)
            answer_numbers = set(answers)
            missing_q = sorted(q_numbers - question_numbers)
            if missing_q:
                sample = ", ".join(f"Q{num}" for num in missing_q[:3])
                if len(missing_q) > 3:
                    sample = f"{sample}..."
                raise AnalystValidationError(
                    f"BLOCK: AIDD:OPEN_QUESTIONS contains {sample}, but matching 'Question N' entries are missing."
                )
            missing_answer = sorted(q_numbers - answer_numbers)
            if missing_answer:
                sample = ", ".join(f"Q{num}" for num in missing_answer[:3])
                if len(missing_answer) > 3:
                    sample = f"{sample}..."
                raise AnalystValidationError(
                    f"BLOCK: AIDD:OPEN_QUESTIONS contains {sample}, but matching 'Answer N' entries are missing."
                )

    if settings.check_open_questions and status == "READY":
        if open_section:
            for line in open_section.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("- [ ]"):
                    raise AnalystValidationError(
                        "BLOCK: status is READY, but 'Open Questions' still has unchecked items."
                    )
        if aidd_open_section and _has_open_items(aidd_open_section):
            raise AnalystValidationError(
                "BLOCK: status is READY, but AIDD:OPEN_QUESTIONS still has open items."
            )

    missing_answers = sorted(set(questions) - set(answers))
    if missing_answers:
        sample = ", ".join(str(num) for num in missing_answers[:3])
        if len(missing_answers) > 3:
            sample += ", …"
        raise AnalystValidationError(
            f"BLOCK: missing answers for questions {sample}. Reply in 'Answer N: ...' format and rerun /feature-dev-aidd:idea-new {ticket}."
        )

    extra_answers = sorted(set(answers) - set(questions))
    if extra_answers:
        sample = ", ".join(str(num) for num in extra_answers[:3])
        if len(extra_answers) > 3:
            sample += ", …"
        raise AnalystValidationError(
            f"BLOCK: found answers without matching questions ({sample}). Align 'Question N' with 'Answer N'."
        )

    if status is None:
        raise AnalystValidationError(
            f"BLOCK: missing `Status:` line in PRD -> update section `{DIALOG_HEADING}`."
        )
    if status == "DRAFT":
        raise AnalystValidationError(
            "BLOCK: PRD status is draft. Complete analyst dialog and set Status: READY before analyst-check."
        )
    if status not in ALLOWED_STATUSES:
        raise AnalystValidationError(
            f"BLOCK: invalid status (`{status}`), expected READY|BLOCKED|PENDING."
        )

    require_ready = settings.require_ready
    if require_ready_override is not None:
        require_ready = require_ready_override

    allow_blocked = settings.allow_blocked
    if allow_blocked_override is not None:
        allow_blocked = allow_blocked_override

    if require_ready and status != "READY":
        if status == "BLOCKED" and not allow_blocked:
            raise AnalystValidationError(
                f"BLOCK: PRD is marked Status: {status}. Resolve open questions and move the cycle to READY."
            )
        if status == "PENDING":
            raise AnalystValidationError("BLOCK: status is PENDING. Close open questions and set Status: READY.")

    research_ref = RESEARCH_REF_TEMPLATE.format(ticket=ticket)
    if research_ref not in text:
        raise AnalystValidationError(
            f"BLOCK: PRD must reference `{research_ref}` in section `{DIALOG_HEADING}` -> add the Researcher report link."
        )

    return AnalystCheckSummary(status=status, question_count=len(set(questions)), answered_count=len(set(answers)))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate analyst dialog state for the active feature PRD.",
    )
    parser.add_argument("--ticket", "--slug", dest="ticket", required=True, help="Feature ticket to validate (alias: --slug).")
    parser.add_argument(
        "--branch",
        help="Current Git branch (used to evaluate branch/skip rules in config/gates.json).",
    )
    parser.add_argument(
        "--allow-blocked",
        action="store_true",
        help="Allow Status: BLOCKED without failing validation.",
    )
    parser.add_argument(
        "--no-ready-required",
        action="store_true",
        help="Do not enforce Status: READY; useful for diagnostics mid-dialog.",
    )
    parser.add_argument(
        "--min-questions",
        type=int,
        help="Override minimum number of questions expected from analyst.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = resolve_aidd_root(Path.cwd())
    settings = load_settings(root)
    try:
        summary = validate_prd(
            root,
            args.ticket,
            settings=settings,
            branch=args.branch,
            require_ready_override=False if args.no_ready_required else None,
            allow_blocked_override=True if args.allow_blocked else None,
            min_questions_override=args.min_questions,
        )
    except AnalystValidationError as exc:
        parser.exit(1, f"{exc}\n")
    if summary.status is None:
        print("analyst gate disabled - nothing to validate.")
    else:
        print(
            f"analyst dialog OK (status: {summary.status}, questions: {summary.question_count})"
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
