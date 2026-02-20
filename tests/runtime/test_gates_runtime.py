from __future__ import annotations

from pathlib import Path

from aidd_runtime import gate_workflow, gates


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
