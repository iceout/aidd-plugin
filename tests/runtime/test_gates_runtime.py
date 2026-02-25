from __future__ import annotations

from pathlib import Path

from aidd_runtime import gate_workflow, gates
from aidd_runtime.analyst_guard import AnalystSettings, validate_prd
from aidd_runtime.prd_review import extract_review_section
from aidd_runtime.prd_review_gate import extract_dialog_status
from aidd_runtime.prd_review_gate import parse_review_section as parse_prd_review_section


def test_select_file_path_prefers_src() -> None:
    paths = ["docs/readme.md", "src/main/kotlin/App.kt", "lib/util.py"]
    assert gate_workflow._select_file_path(paths) == "src/main/kotlin/App.kt"


def test_next3_has_real_items_accepts_real_entry(tmp_path: Path) -> None:
    path = tmp_path / "tasklist.md"
    path.write_text("## AIDD:NEXT_3\n- [ ] TASK-1: do it\n", encoding="utf-8")
    assert gate_workflow._next3_has_real_items(path) is True


def test_next3_has_real_items_rejects_placeholders(tmp_path: Path) -> None:
    path = tmp_path / "tasklist.md"
    path.write_text("## AIDD:NEXT_3\n- [ ] <1. task>\n", encoding="utf-8")
    assert gate_workflow._next3_has_real_items(path) is False


def test_resolve_stage_tests_policy_with_defaults() -> None:
    assert gates.resolve_stage_tests_policy({}, "implement") == "none"
    assert gates.resolve_stage_tests_policy({}, "review") == "targeted"
    assert gates.resolve_stage_tests_policy({}, "qa") == "full"


def test_resolve_stage_tests_policy_with_override() -> None:
    config = {"tests_policy": {"implement": "full"}}
    assert gates.resolve_stage_tests_policy(config, "implement") == "full"


def test_branch_enabled_with_allow_and_skip_patterns() -> None:
    assert gates.branch_enabled("feature/demo", allow=["feature/*"], skip=["docs/*"]) is True
    assert gates.branch_enabled("docs/readme", allow=["feature/*"], skip=["docs/*"]) is False


def test_analyst_guard_accepts_new_dialog_heading(tmp_path: Path) -> None:
    root = tmp_path / "aidd"
    prd_path = root / "docs" / "prd" / "T-100.prd.md"
    prd_path.parent.mkdir(parents=True, exist_ok=True)
    prd_path.write_text(
        "\n".join(
            [
                "# PRD",
                "",
                "## Analyst dialogue",
                "Question 1: What is the scope?",
                "Answer 1: MVP only.",
                "Status: READY",
                "",
                "## AIDD:OPEN_QUESTIONS",
                "none",
                "",
                "## Links",
                f"- Research: `docs/research/T-100.md`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = validate_prd(root, "T-100", settings=AnalystSettings())
    assert summary.status == "READY"
    assert summary.question_count == 1


def test_prd_review_gate_extracts_status_from_new_dialog_heading() -> None:
    content = "\n".join(
        [
            "# PRD",
            "",
            "## Analyst dialogue",
            "Status: READY",
            "",
            "## PRD Review",
            "Status: READY",
        ]
    )
    assert extract_dialog_status(content) == "ready"


def test_prd_review_parser_accepts_numbered_review_heading() -> None:
    content = "\n".join(
        [
            "# PRD",
            "",
            "## 11. PRD Review",
            "Status: READY",
            "- [x] Reviewer confirms scope",
            "- [ ] Follow-up item",
        ]
    )
    status, action_items = extract_review_section(content)
    assert status == "ready"
    assert action_items == ["- [x] Reviewer confirms scope", "- [ ] Follow-up item"]


def test_prd_review_gate_parser_accepts_numbered_review_heading() -> None:
    content = "\n".join(
        [
            "# PRD",
            "",
            "## 11. PRD Review",
            "Status: READY",
            "- [ ] Pending item",
        ]
    )
    found, status, action_items = parse_prd_review_section(content)
    assert found is True
    assert status == "ready"
    assert action_items == ["- [ ] Pending item"]
