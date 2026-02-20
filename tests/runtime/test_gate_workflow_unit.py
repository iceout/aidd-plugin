from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd_runtime import gate_workflow
from aidd_runtime import runtime as runtime_module


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_select_file_path_prefers_src_and_fallback() -> None:
    paths = ["docs/readme.md", "src/app/main.py", "lib/util.py"]
    assert gate_workflow._select_file_path(paths) == "src/app/main.py"
    assert gate_workflow._select_file_path(["docs/a.md", "lib/b.py"]) == "docs/a.md"
    assert gate_workflow._select_file_path([]) == ""


def test_next3_has_real_items_variants(tmp_path: Path) -> None:
    tasklist = tmp_path / "tasklist.md"
    tasklist.write_text(
        "\n".join(
            [
                "## AIDD:NEXT_3",
                "- [ ] <ticket>: placeholder",
                "- [ ] TASK-1 do work",
            ]
        ),
        encoding="utf-8",
    )
    assert gate_workflow._next3_has_real_items(tasklist) is True

    tasklist.write_text("## AIDD:NEXT_3\n- [ ] <1. task>\n", encoding="utf-8")
    assert gate_workflow._next3_has_real_items(tasklist) is False

    tasklist.write_text("## AIDD:NEXT_3\n- (none)\n", encoding="utf-8")
    assert gate_workflow._next3_has_real_items(tasklist) is True


def test_is_skill_first(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    assert gate_workflow._is_skill_first(plugin_root) is False

    _write(plugin_root / "skills" / "aidd-core" / "SKILL.md", "# core\n")
    assert gate_workflow._is_skill_first(plugin_root) is False

    _write(plugin_root / "skills" / "implement" / "SKILL.md", "# implement\n")
    assert gate_workflow._is_skill_first(plugin_root) is True


def test_loop_scope_key_changes_by_stage(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "aidd"
    root.mkdir()

    monkeypatch.setattr(runtime_module, "read_active_work_item", lambda _root: "I-17")
    monkeypatch.setattr(runtime_module, "resolve_scope_key", lambda raw, ticket: raw or ticket)

    assert gate_workflow._loop_scope_key(root, "TK-1", "implement") == "I-17"
    assert gate_workflow._loop_scope_key(root, "TK-1", "qa") == "TK-1"


def test_reviewer_notice_behaviors(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "aidd"
    _write(
        root / "config" / "gates.json",
        json.dumps(
            {
                "reviewer": {
                    "enabled": True,
                    "tests_field": "tests",
                    "required_values": ["required"],
                    "optional_values": ["optional"],
                    "warn_on_missing": True,
                }
            }
        ),
    )

    marker = root / "reports" / "reviewer" / "TK-1" / "scope.tests.json"
    monkeypatch.setattr(runtime_module, "read_active_work_item", lambda _root: "scope")
    monkeypatch.setattr(runtime_module, "resolve_scope_key", lambda *_args, **_kwargs: "scope")
    monkeypatch.setattr(
        runtime_module,
        "reviewer_marker_path",
        lambda *_args, **_kwargs: marker,
    )

    warn_missing = gate_workflow._reviewer_notice(root, "TK-1", "")
    assert warn_missing.startswith("WARN:")

    _write(marker, json.dumps({"tests": "required"}))
    blocked = gate_workflow._reviewer_notice(root, "TK-1", "")
    assert blocked.startswith("BLOCK:")

    _write(marker, json.dumps({"tests": "unexpected"}))
    invalid = gate_workflow._reviewer_notice(root, "TK-1", "")
    assert "invalid reviewer marker status" in invalid


def test_handoff_block_requires_tasklist_links(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "aidd"
    _write(
        root / "config" / "gates.json",
        json.dumps({"qa": {"report": "aidd/reports/qa/{ticket}.json"}}),
    )
    _write(root / "reports" / "qa" / "TK-2.json", json.dumps({"status": "PASS"}))

    tasklist = root / "docs" / "tasklist" / "TK-2.md"
    _write(tasklist, "## AIDD:HANDOFF_INBOX\n- [ ] nothing\n")

    monkeypatch.setattr(runtime_module, "read_active_work_item", lambda _root: "scope")
    monkeypatch.setattr(runtime_module, "resolve_scope_key", lambda *_args, **_kwargs: "scope")
    monkeypatch.setattr(
        runtime_module,
        "reviewer_marker_path",
        lambda *_args, **_kwargs: root / "reports" / "reviewer" / "TK-2" / "scope.tests.json",
    )
    monkeypatch.setattr(
        runtime_module,
        "review_report_template",
        lambda _root: "aidd/reports/reviewer/{ticket}/{scope_key}.tests.json",
    )

    msg = gate_workflow._handoff_block(root, "TK-2", "", "feature/tk2", tasklist)
    assert msg.startswith("BLOCK:")
    assert "handoff tasks" in msg

    tasklist.write_text(
        "\n".join(
            [
                "## AIDD:HANDOFF_INBOX",
                "- [ ] source: qa",
                "- [ ] aidd/reports/qa/TK-2.json",
            ]
        ),
        encoding="utf-8",
    )
    msg2 = gate_workflow._handoff_block(root, "TK-2", "", "feature/tk2", tasklist)
    assert msg2 == ""
