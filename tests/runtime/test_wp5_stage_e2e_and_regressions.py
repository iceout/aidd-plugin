from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from aidd_runtime import command_runner, stage_dispatch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INIT_SCRIPT = PROJECT_ROOT / "skills" / "aidd-init" / "runtime" / "init.py"
HOOK_SCRIPT = PROJECT_ROOT / "hooks" / "gate-workflow.sh"


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        input="",
        check=False,
    )


def _run_init(workspace: Path) -> None:
    env = os.environ.copy()
    env["AIDD_ROOT"] = str(PROJECT_ROOT)
    proc = _run([sys.executable, str(INIT_SCRIPT), "--force"], cwd=workspace, env=env)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def _configure_relaxed_gates(workspace: Path) -> None:
    gates_path = workspace / "aidd" / "config" / "gates.json"
    payload = json.loads(gates_path.read_text(encoding="utf-8"))
    payload["analyst"] = {"enabled": False}
    payload["researcher"] = {
        "enabled": True,
        "require_status": ["pending", "reviewed"],
        "minimum_paths": 1,
        "freshness_days": 365,
        "allow_missing": False,
    }
    payload["rlm"] = {
        "enabled": False,
        "require_pack": False,
        "require_nodes": False,
        "require_links": False,
        "required_for_langs": [],
    }
    gates_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _write_prd_missing_hints(workspace: Path, ticket: str) -> None:
    prd_path = workspace / "aidd" / "docs" / "prd" / f"{ticket}.prd.md"
    prd_path.parent.mkdir(parents=True, exist_ok=True)
    prd_path.write_text(
        (
            f"# PRD — {ticket}\n\n"
            "Status: READY\n"
            f"Ticket: {ticket}\n\n"
            "## AIDD:ANSWERS\n"
            "- Answer 1: minimal answer\n"
        ),
        encoding="utf-8",
    )


def _write_prd_with_research_hints(workspace: Path, ticket: str) -> None:
    prd_path = workspace / "aidd" / "docs" / "prd" / f"{ticket}.prd.md"
    prd_path.parent.mkdir(parents=True, exist_ok=True)
    prd_path.write_text(
        (
            f"# PRD — {ticket}\n\n"
            "Status: READY\n"
            f"Ticket: {ticket}\n\n"
            "## AIDD:ANSWERS\n"
            "- Answer 1: minimal answer\n\n"
            "## AIDD:RESEARCH_HINTS\n"
            "- Paths: docs,config\n"
            "- Keywords: stage,dispatch\n"
            "- Notes: wp5 integration fixture\n"
        ),
        encoding="utf-8",
    )


@pytest.fixture()
def wp5_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _run_init(workspace)
    return workspace


def test_failure_e2e_missing_ticket_dispatch_raises(wp5_workspace: Path) -> None:
    with pytest.raises(ValueError, match="ticket is required"):
        stage_dispatch.dispatch_stage_command(
            "/skill:plan-new",
            cwd=wp5_workspace,
            check=False,
        )


def test_failure_e2e_research_missing_hints_via_dispatch(wp5_workspace: Path) -> None:
    ticket = "WP5-MISS-HINTS-001"
    _configure_relaxed_gates(wp5_workspace)
    _write_prd_missing_hints(wp5_workspace, ticket)

    result = stage_dispatch.dispatch_stage_command(
        "/skill:researcher",
        ticket=ticket,
        argv=["--auto"],
        cwd=wp5_workspace,
        check=False,
    )
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode != 0
    assert "AIDD:RESEARCH_HINTS" in output
    assert "cannot import name" not in output


def test_failure_e2e_blocked_gate_short_circuits_before_stage_command(wp5_workspace: Path) -> None:
    ticket = "WP5-BLOCK-001"
    result = stage_dispatch.dispatch_stage_command(
        "/skill:qa",
        ticket=ticket,
        cwd=wp5_workspace,
        check=False,
    )
    assert result.returncode != 0
    assert result.command == ()
    assert "BLOCK:" in result.stderr
    assert "cannot import name" not in (result.stdout + result.stderr)


def test_hooks_plus_stage_orchestration_combined_smoke(wp5_workspace: Path) -> None:
    ticket = "WP5-CHAIN-001"
    _configure_relaxed_gates(wp5_workspace)

    idea = stage_dispatch.dispatch_stage_command(
        "/skill:idea-new",
        ticket=ticket,
        cwd=wp5_workspace,
        check=True,
    )
    assert idea.returncode == 0

    _write_prd_with_research_hints(wp5_workspace, ticket)

    research = stage_dispatch.dispatch_stage_command(
        "/skill:researcher",
        ticket=ticket,
        argv=["--auto"],
        cwd=wp5_workspace,
        check=True,
    )
    assert research.returncode == 0

    plan = stage_dispatch.dispatch_stage_command(
        "/skill:plan-new",
        ticket=ticket,
        cwd=wp5_workspace,
        check=True,
    )
    assert plan.returncode == 0

    tasks = stage_dispatch.dispatch_stage_command(
        "/skill:tasks-new",
        ticket=ticket,
        argv=["--force-template"],
        cwd=wp5_workspace,
        check=True,
    )
    assert tasks.returncode == 0
    assert (wp5_workspace / "aidd" / "docs" / "tasklist" / f"{ticket}.md").exists()

    env = os.environ.copy()
    env["AIDD_ROOT"] = str(PROJECT_ROOT)
    env["AIDD_HOOKS_MODE"] = "fast"
    env["HOOK_PAYLOAD"] = json.dumps({"cwd": str(wp5_workspace)})
    hook_proc = _run([sys.executable, str(HOOK_SCRIPT)], cwd=wp5_workspace, env=env)
    output = f"{hook_proc.stdout}\n{hook_proc.stderr}"
    assert hook_proc.returncode in {0, 2}
    assert "cannot import name" not in output


def test_regression_resolve_dispatch_target_codex_legacy_alias_combo() -> None:
    target = stage_dispatch.resolve_dispatch_target("$flow:aidd-plan-flow")
    assert target.requested_command == "aidd-plan-flow"
    assert target.resolved_command == "plan-new"
    assert target.is_legacy_alias is True


def test_regression_dispatch_profile_auto_detection_in_stage_dispatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workspace = tmp_path / "workspace"
    project_root = workspace / "aidd"
    workspace.mkdir(parents=True, exist_ok=True)
    project_root.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(stage_dispatch.runtime, "require_plugin_root", lambda: PROJECT_ROOT)
    monkeypatch.setattr(
        stage_dispatch.runtime, "require_workflow_root", lambda _cwd=None: (workspace, project_root)
    )
    monkeypatch.setattr(stage_dispatch.runtime, "read_active_slug", lambda _root: "")
    monkeypatch.setattr(stage_dispatch, "_run_state_script", lambda *args, **kwargs: None)
    monkeypatch.setattr(stage_dispatch, "_run_preflight_if_enabled", lambda *args, **kwargs: None)

    seen_profiles: list[str] = []

    def fake_build_runtime_env(plugin_root: Path, *, profile=None, **_kwargs):  # type: ignore[no-untyped-def]
        name = stage_dispatch.ide_profiles.resolve_profile(profile).name
        seen_profiles.append(f"env:{name}")
        return {"AIDD_ROOT": str(plugin_root), "AIDD_IDE_PROFILE": name}

    def fake_run_command(command, *, cwd, profile=None, env=None, check=False, error_context=None, **_kwargs):  # type: ignore[no-untyped-def]
        profile_name = stage_dispatch.ide_profiles.resolve_profile(profile).name
        seen_profiles.append(f"run:{profile_name}")
        return command_runner.CommandResult(
            command=tuple(str(part) for part in command),
            cwd=cwd,
            returncode=0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(stage_dispatch.command_runner, "build_runtime_env", fake_build_runtime_env)
    monkeypatch.setattr(stage_dispatch.command_runner, "run_command", fake_run_command)

    result_codex = stage_dispatch.dispatch_stage_command(
        "$aidd:plan-new",
        ticket="WP5-PROFILE-1",
        cwd=workspace,
        check=False,
    )
    assert result_codex.profile == "codex"

    monkeypatch.setenv("AIDD_IDE_PROFILE", "cursor")
    result_cursor = stage_dispatch.dispatch_stage_command(
        "/skill:plan-new",
        ticket="WP5-PROFILE-2",
        cwd=workspace,
        check=False,
    )
    assert result_cursor.profile == "cursor"
    assert "env:codex" in seen_profiles
    assert "run:codex" in seen_profiles
    assert "env:cursor" in seen_profiles
    assert "run:cursor" in seen_profiles
