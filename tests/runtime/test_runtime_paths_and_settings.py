from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd_runtime import runtime


def test_resolve_roots_and_require_workflow_root(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    resolved_workspace, project_root = runtime.resolve_roots(workspace, create=True)
    assert resolved_workspace == workspace
    assert project_root == workspace / "aidd"
    assert project_root.exists()

    with pytest.raises(FileNotFoundError, match="workflow files not found"):
        runtime.require_workflow_root(workspace)

    (project_root / "docs").mkdir(parents=True, exist_ok=True)
    required_workspace, required_project = runtime.require_workflow_root(workspace)
    assert required_workspace == workspace
    assert required_project == project_root


def test_plugin_workspace_guard_blocks_plugin_repo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    plugin_root = tmp_path / "plugin"
    plugin_root.mkdir()
    (plugin_root / ".aidd-plugin").write_text("1\n", encoding="utf-8")

    monkeypatch.setenv("AIDD_ROOT", str(plugin_root))
    with pytest.raises(RuntimeError, match="refusing to use plugin repository"):
        runtime.resolve_roots(plugin_root, create=True)


def test_auto_index_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AIDD_INDEX_AUTO", raising=False)
    assert runtime.auto_index_enabled() is True

    monkeypatch.setenv("AIDD_INDEX_AUTO", "off")
    assert runtime.auto_index_enabled() is False

    monkeypatch.setenv("AIDD_INDEX_AUTO", "yes")
    assert runtime.auto_index_enabled() is True


def test_resolve_path_for_target_and_rel_path(tmp_path: Path) -> None:
    target = tmp_path / "aidd"
    target.mkdir()

    absolute = tmp_path / "abs.md"
    absolute.write_text("x", encoding="utf-8")
    assert runtime.resolve_path_for_target(absolute, target) == absolute.resolve()

    dot_rel = runtime.resolve_path_for_target(Path("./docs/file.md"), target)
    assert dot_rel == (target / "docs" / "file.md").resolve()

    prefixed = runtime.resolve_path_for_target(Path("aidd/reports/out.json"), target)
    assert prefixed == (target / "reports" / "out.json").resolve()

    assert runtime.rel_path(target / "docs" / "x.md", target) == "aidd/docs/x.md"
    assert runtime.rel_path(target / "docs" / "x.md", tmp_path) == "aidd/docs/x.md"


def test_load_json_settings_and_tests_config(tmp_path: Path) -> None:
    payload_path = tmp_path / "payload.json"
    payload_path.write_text('{"ok": true}', encoding="utf-8")
    assert runtime.load_json_file(payload_path) == {"ok": True}

    list_path = tmp_path / "list.json"
    list_path.write_text("[]", encoding="utf-8")
    assert runtime.load_json_file(list_path) == {}

    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="failed to parse"):
        runtime.load_json_file(bad_path)

    target = tmp_path / "aidd"
    target.mkdir()
    settings_file = tmp_path / ".aidd" / "settings.json"
    settings_file.parent.mkdir(parents=True, exist_ok=True)

    assert runtime.load_settings_json(target) == {}

    settings_file.write_text("{", encoding="utf-8")
    with pytest.raises(RuntimeError, match="cannot parse"):
        runtime.load_settings_json(target)

    settings_file.write_text(
        json.dumps(
            {
                "automation": {
                    "tests": {
                        "cadence": "checkpoint",
                        "checkpointTrigger": ["progress", "stop"],
                        "reviewerGate": {"enabled": True},
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    tests_cfg = runtime.load_tests_settings(target)
    assert tests_cfg.get("cadence") == "checkpoint"
    assert runtime.reviewer_gate_config(target) == {"enabled": True}


def test_checkpoint_settings_and_write(tmp_path: Path) -> None:
    target = tmp_path / "aidd"
    target.mkdir()
    settings_file = tmp_path / ".aidd" / "settings.json"
    settings_file.parent.mkdir(parents=True, exist_ok=True)

    settings_file.write_text(
        json.dumps(
            {
                "automation": {
                    "tests": {
                        "cadence": "checkpoint",
                        "checkpoint_trigger": "progress, stop",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    assert runtime.normalize_checkpoint_triggers(None) == ["progress"]
    assert runtime.normalize_checkpoint_triggers(["A", " ", "B"]) == ["a", "b"]

    runtime.maybe_write_test_checkpoint(
        target,
        ticket="TK-001",
        slug_hint="tk-001",
        source="unit-test",
    )
    checkpoint_path = target / ".cache" / "test-checkpoint.json"
    assert checkpoint_path.exists()

    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert payload["ticket"] == "TK-001"
    assert payload["trigger"] == "progress"


def test_review_report_template_and_marker_migration(tmp_path: Path) -> None:
    target = tmp_path / "aidd"
    target.mkdir()

    config_dir = target / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Missing {scope_key} should fall back to default template.
    (config_dir / "gates.json").write_text(
        json.dumps({"reviewer": {"review_report": "aidd/reports/reviewer/{ticket}.json"}}),
        encoding="utf-8",
    )
    assert runtime.review_report_template(target) == runtime.DEFAULT_REVIEW_REPORT

    template = "aidd/reports/reviewer/{ticket}/{scope_key}.tests.json"
    (config_dir / "gates.json").write_text(
        json.dumps({"reviewer": {"review_report": template}}),
        encoding="utf-8",
    )
    assert runtime.review_report_template(target) == template

    expected_marker = target / "reports" / "reviewer" / "TK-1" / "scope.tests.json"
    expected_marker.parent.mkdir(parents=True, exist_ok=True)
    legacy_path = expected_marker.with_name("scope.json")
    legacy_path.write_text(json.dumps({"legacy": True}), encoding="utf-8")

    marker = runtime.reviewer_marker_path(
        target,
        template=template,
        ticket="TK-1",
        slug_hint=None,
        scope_key="scope",
    )
    assert marker == expected_marker
    assert marker.exists()
    assert not legacy_path.exists()

    with pytest.raises(ValueError, match="escapes project root"):
        runtime.reviewer_marker_path(
            target,
            template="../../escape/{scope_key}.tests.json",
            ticket="TK-1",
            slug_hint=None,
            scope_key="scope",
        )


def test_scope_and_tool_result_helpers() -> None:
    assert runtime.sanitize_scope_key("  I-1 / fix ") == "I-1_fix"
    assert runtime.resolve_scope_key("", "TK-2") == "TK-2"
    assert runtime.resolve_scope_key(None, "") == "ticket"

    resolved, warn = runtime.resolve_tool_result_id({"id": "r-1"})
    assert resolved == "r-1"
    assert warn == ""

    resolved2, warn2 = runtime.resolve_tool_result_id({"request_id": "req-1"})
    assert resolved2 == "tool_result:req-1"
    assert "tool_result_missing_id" in warn2

    resolved3, warn3 = runtime.resolve_tool_result_id({}, index=7)
    assert resolved3 == "tool_result:7"
    assert warn3
