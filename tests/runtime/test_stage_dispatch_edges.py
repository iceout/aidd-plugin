from __future__ import annotations

import sys
from pathlib import Path

import pytest

from aidd_runtime import command_runner, readiness_gates, stage_dispatch


def _prepare_fake_plugin(tmp_path: Path) -> Path:
    plugin_root = tmp_path / "plugin"
    entrypoint = plugin_root / "skills" / "idea-new" / "runtime" / "analyst_check.py"
    entrypoint.parent.mkdir(parents=True, exist_ok=True)
    entrypoint.write_text("print('idea')\n", encoding="utf-8")
    return plugin_root


def _patch_dispatch_runtime(
    monkeypatch: pytest.MonkeyPatch,
    *,
    plugin_root: Path,
    workspace_root: Path,
    project_root: Path,
    preflight_result: readiness_gates.GateResult | None = None,
) -> None:
    monkeypatch.setattr(stage_dispatch.runtime, "require_plugin_root", lambda: plugin_root)
    monkeypatch.setattr(
        stage_dispatch.runtime,
        "require_workflow_root",
        lambda cwd=None: (workspace_root, project_root),
    )
    monkeypatch.setattr(stage_dispatch, "_run_state_script", lambda *args, **kwargs: None)

    if preflight_result is None:
        monkeypatch.setattr(
            stage_dispatch, "_run_preflight_if_enabled", lambda *args, **kwargs: None
        )
    else:
        monkeypatch.setattr(
            stage_dispatch,
            "_run_preflight_if_enabled",
            lambda *args, **kwargs: preflight_result,
        )

    monkeypatch.setattr(
        stage_dispatch.command_runner,
        "build_runtime_env",
        lambda _plugin_root, **kwargs: {"AIDD_ROOT": str(plugin_root)},
    )


def test_dispatch_injects_ticket_flag_when_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    plugin_root = _prepare_fake_plugin(tmp_path)
    workspace_root = tmp_path / "ws"
    project_root = workspace_root / "aidd"
    project_root.mkdir(parents=True, exist_ok=True)

    _patch_dispatch_runtime(
        monkeypatch,
        plugin_root=plugin_root,
        workspace_root=workspace_root,
        project_root=project_root,
    )

    captured: dict[str, tuple[str, ...]] = {}

    def _fake_run_command(command, **kwargs):  # noqa: ANN001
        captured["command"] = tuple(str(part) for part in command)
        return command_runner.CommandResult(
            command=tuple(str(part) for part in command),
            cwd=kwargs["cwd"],
            returncode=0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(stage_dispatch.command_runner, "run_command", _fake_run_command)

    result = stage_dispatch.dispatch_stage_command(
        "/skill:idea-new",
        ticket="EDGE-1001",
        argv=["--note", "demo"],
        cwd=workspace_root,
        check=True,
    )

    assert result.returncode == 0
    command = captured["command"]
    assert command[0] == sys.executable
    assert "--ticket" in command
    idx = command.index("--ticket")
    assert command[idx + 1] == "EDGE-1001"


def test_dispatch_does_not_duplicate_ticket_flag(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    plugin_root = _prepare_fake_plugin(tmp_path)
    workspace_root = tmp_path / "ws"
    project_root = workspace_root / "aidd"
    project_root.mkdir(parents=True, exist_ok=True)

    _patch_dispatch_runtime(
        monkeypatch,
        plugin_root=plugin_root,
        workspace_root=workspace_root,
        project_root=project_root,
    )

    captured: dict[str, tuple[str, ...]] = {}

    def _fake_run_command(command, **kwargs):  # noqa: ANN001
        captured["command"] = tuple(str(part) for part in command)
        return command_runner.CommandResult(
            command=tuple(str(part) for part in command),
            cwd=kwargs["cwd"],
            returncode=0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(stage_dispatch.command_runner, "run_command", _fake_run_command)

    stage_dispatch.dispatch_stage_command(
        "/skill:idea-new",
        ticket="EDGE-1002",
        argv=["--ticket", "FROM-ARGV", "--x"],
        cwd=workspace_root,
        check=True,
    )

    command = captured["command"]
    assert command.count("--ticket") == 1
    idx = command.index("--ticket")
    assert command[idx + 1] == "FROM-ARGV"


def test_dispatch_returns_preflight_block_without_command_execution(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    plugin_root = _prepare_fake_plugin(tmp_path)
    workspace_root = tmp_path / "ws"
    project_root = workspace_root / "aidd"
    project_root.mkdir(parents=True, exist_ok=True)

    _patch_dispatch_runtime(
        monkeypatch,
        plugin_root=plugin_root,
        workspace_root=workspace_root,
        project_root=project_root,
        preflight_result=readiness_gates.GateResult(
            name="tasklist_check",
            returncode=2,
            output="BLOCK: preflight fail",
        ),
    )

    def _should_not_run(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("run_command should not be called when preflight blocks")

    monkeypatch.setattr(stage_dispatch.command_runner, "run_command", _should_not_run)

    result = stage_dispatch.dispatch_stage_command(
        "/skill:idea-new",
        ticket="EDGE-1003",
        cwd=workspace_root,
        check=False,
    )
    assert result.returncode == 2
    assert "BLOCK: preflight fail" in result.stderr
    assert result.command == ()


def test_preflight_enablement_helpers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = stage_dispatch.resolve_dispatch_target("/skill:implement")

    monkeypatch.setenv("AIDD_STAGE_DISPATCH_GATES", "0")
    monkeypatch.setattr(
        stage_dispatch.readiness_gates,
        "run_stage_preflight",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not run")),
    )
    disabled = stage_dispatch._run_preflight_if_enabled(
        target,
        project_root=tmp_path,
        ticket="EDGE-1004",
        slug_hint="",
    )
    assert disabled is None

    monkeypatch.setenv("AIDD_STAGE_DISPATCH_GATES", "1")
    no_ticket = stage_dispatch._run_preflight_if_enabled(
        target,
        project_root=tmp_path,
        ticket="",
        slug_hint="",
    )
    assert no_ticket is None

    monkeypatch.setattr(stage_dispatch.runtime, "detect_branch", lambda _root: "feature/test")
    monkeypatch.setattr(
        stage_dispatch.readiness_gates,
        "run_stage_preflight",
        lambda *args, **kwargs: readiness_gates.GateResult(
            name="preflight",
            returncode=0,
            output=kwargs["branch"],
        ),
    )
    enabled = stage_dispatch._run_preflight_if_enabled(
        target,
        project_root=tmp_path,
        ticket="EDGE-1004",
        slug_hint="hint",
    )
    assert enabled is not None
    assert enabled.output == "feature/test"


def test_internal_flag_and_normalization_helpers() -> None:
    assert stage_dispatch._contains_flag(["--ticket", "T-1"], "--ticket") is True
    assert stage_dispatch._contains_flag(["--ticket=T-2"], "--ticket") is True
    assert stage_dispatch._contains_flag(["--x", "1"], "--ticket") is False

    assert stage_dispatch.normalize_command_name("/skill:plan_new") == "plan-new"
    assert stage_dispatch.normalize_command_name("  /flow:aidd-plan-flow  ") == "aidd-plan-flow"
