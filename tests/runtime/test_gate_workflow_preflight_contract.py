from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd_runtime import gate_workflow


def _write(path: Path, text: str = "{}\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _prepare_plugin_root(tmp_path: Path) -> Path:
    plugin_root = tmp_path / "plugin"
    _write(plugin_root / "skills" / "aidd-core" / "SKILL.md", "# core\n")
    _write(plugin_root / "skills" / "implement" / "SKILL.md", "# implement\n")
    return plugin_root


def _write_active_state(root: Path, *, ticket: str, stage: str, work_item: str) -> None:
    _write(
        root / "docs" / ".active.json",
        json.dumps(
            {
                "ticket": ticket,
                "slug_hint": ticket,
                "stage": stage,
                "work_item": work_item,
            }
        )
        + "\n",
    )


def _write_required_artifacts(root: Path, *, ticket: str, stage: str, scope_key: str) -> None:
    _write(root / "reports" / "actions" / ticket / scope_key / f"{stage}.actions.template.json")
    _write(root / "reports" / "actions" / ticket / scope_key / f"{stage}.actions.json")
    _write(root / "reports" / "context" / ticket / f"{scope_key}.readmap.json")
    _write(root / "reports" / "context" / ticket / f"{scope_key}.readmap.md", "# readmap\n")
    _write(root / "reports" / "context" / ticket / f"{scope_key}.writemap.json")
    _write(root / "reports" / "context" / ticket / f"{scope_key}.writemap.md", "# writemap\n")
    _write(root / "reports" / "loops" / ticket / scope_key / "stage.preflight.result.json")
    _write(root / "reports" / "logs" / stage / ticket / scope_key / "wrapper.preflight.log", "ok\n")


def _write_output_contract(
    root: Path,
    *,
    ticket: str,
    scope_key: str,
    payload: dict[str, object],
) -> None:
    _write(
        root / "reports" / "loops" / ticket / scope_key / "output.contract.json",
        json.dumps(payload) + "\n",
    )


def test_preflight_guard_blocks_when_artifacts_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    plugin_root = _prepare_plugin_root(tmp_path)
    root = tmp_path / "workspace" / "aidd"
    root.mkdir(parents=True, exist_ok=True)
    _write_active_state(root, ticket="TK-P1", stage="implement", work_item="I1")

    monkeypatch.setenv("AIDD_ROOT", str(plugin_root))
    ok, message = gate_workflow._loop_preflight_guard(root, "TK-P1", "implement", "strict")
    assert ok is False
    assert "reason_code=preflight_missing" in message


def test_preflight_guard_accepts_complete_contract(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    plugin_root = _prepare_plugin_root(tmp_path)
    root = tmp_path / "workspace" / "aidd"
    root.mkdir(parents=True, exist_ok=True)
    ticket = "TK-P2"
    stage = "implement"
    scope = "I2"
    _write_active_state(root, ticket=ticket, stage=stage, work_item=scope)
    _write_required_artifacts(root, ticket=ticket, stage=stage, scope_key=scope)
    _write_output_contract(
        root,
        ticket=ticket,
        scope_key=scope,
        payload={
            "status": "ok",
            "actions_log": f"aidd/reports/actions/{ticket}/{scope}/{stage}.actions.json",
        },
    )

    monkeypatch.setenv("AIDD_ROOT", str(plugin_root))
    ok, message = gate_workflow._loop_preflight_guard(root, ticket, stage, "strict")
    assert ok is True
    assert message == ""


def test_preflight_guard_wrappers_skip_behavior(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    plugin_root = _prepare_plugin_root(tmp_path)
    root = tmp_path / "workspace" / "aidd"
    root.mkdir(parents=True, exist_ok=True)
    _write_active_state(root, ticket="TK-P3", stage="implement", work_item="I3")
    _write_required_artifacts(root, ticket="TK-P3", stage="implement", scope_key="I3")

    monkeypatch.setenv("AIDD_ROOT", str(plugin_root))
    monkeypatch.setenv("AIDD_SKIP_STAGE_WRAPPERS", "1")

    ok_strict, message_strict = gate_workflow._loop_preflight_guard(
        root, "TK-P3", "implement", "strict"
    )
    assert ok_strict is False
    assert "reason_code=wrappers_skipped_unsafe" in message_strict

    ok_fast, message_fast = gate_workflow._loop_preflight_guard(root, "TK-P3", "implement", "fast")
    assert ok_fast is True
    assert "reason_code=wrappers_skipped_warn" in message_fast


def test_preflight_guard_output_contract_warn_modes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    plugin_root = _prepare_plugin_root(tmp_path)
    root = tmp_path / "workspace" / "aidd"
    root.mkdir(parents=True, exist_ok=True)
    ticket = "TK-P4"
    stage = "implement"
    scope = "I4"
    _write_active_state(root, ticket=ticket, stage=stage, work_item=scope)
    _write_required_artifacts(root, ticket=ticket, stage=stage, scope_key=scope)
    _write_output_contract(
        root,
        ticket=ticket,
        scope_key=scope,
        payload={
            "status": "warn",
            "warnings": ["readmap_mismatch"],
            "actions_log": f"aidd/reports/actions/{ticket}/{scope}/{stage}.actions.json",
        },
    )

    monkeypatch.setenv("AIDD_ROOT", str(plugin_root))
    ok_strict, msg_strict = gate_workflow._loop_preflight_guard(root, ticket, stage, "strict")
    assert ok_strict is False
    assert "reason_code=output_contract_warn" in msg_strict

    ok_fast, msg_fast = gate_workflow._loop_preflight_guard(root, ticket, stage, "fast")
    assert ok_fast is True
    assert "reason_code=output_contract_warn" in msg_fast


def test_preflight_guard_missing_actions_log_handling(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    plugin_root = _prepare_plugin_root(tmp_path)
    root = tmp_path / "workspace" / "aidd"
    root.mkdir(parents=True, exist_ok=True)
    ticket = "TK-P5"
    stage = "implement"
    scope = "I5"
    _write_active_state(root, ticket=ticket, stage=stage, work_item=scope)
    _write_required_artifacts(root, ticket=ticket, stage=stage, scope_key=scope)

    _write_output_contract(root, ticket=ticket, scope_key=scope, payload={"status": "ok"})

    monkeypatch.setenv("AIDD_ROOT", str(plugin_root))
    ok_strict, msg_strict = gate_workflow._loop_preflight_guard(root, ticket, stage, "strict")
    assert ok_strict is False
    assert "reason_code=actions_log_missing" in msg_strict

    ok_fast, msg_fast = gate_workflow._loop_preflight_guard(root, ticket, stage, "fast")
    assert ok_fast is True
    assert "reason_code=actions_log_missing" in msg_fast
