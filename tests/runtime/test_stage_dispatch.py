from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from aidd_runtime import stage_dispatch
from aidd_runtime.feature_ids import read_active_state


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INIT_SCRIPT = PROJECT_ROOT / "skills" / "aidd-init" / "runtime" / "init.py"


@pytest.fixture()
def dispatch_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["AIDD_ROOT"] = str(PROJECT_ROOT)
    proc = subprocess.run(
        [sys.executable, str(INIT_SCRIPT), "--force"],
        cwd=workspace,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return workspace


def test_resolve_dispatch_target_legacy_flow_alias() -> None:
    target = stage_dispatch.resolve_dispatch_target("/flow:aidd-plan-flow")
    assert target.resolved_command == "plan-new"
    assert target.spec.stage == "plan"
    assert target.is_legacy_alias is True


def test_resolve_dispatch_target_codex_style_prefix() -> None:
    target = stage_dispatch.resolve_dispatch_target("$aidd:plan-new")
    assert target.resolved_command == "plan-new"
    assert target.spec.stage == "plan"
    assert target.is_legacy_alias is False


def test_dispatch_tasks_new_updates_active_state(dispatch_workspace: Path) -> None:
    result = stage_dispatch.dispatch_stage_command(
        "/skill:tasks-new",
        ticket="P4-1001",
        argv=["--force-template"],
        cwd=dispatch_workspace,
        check=True,
    )
    assert result.returncode == 0
    assert result.target.resolved_command == "tasks-new"
    assert result.ticket == "P4-1001"

    tasklist_path = dispatch_workspace / "aidd" / "docs" / "tasklist" / "P4-1001.md"
    assert tasklist_path.exists()

    state = read_active_state(dispatch_workspace)
    assert state.ticket == "P4-1001"
    assert state.stage == "tasklist"


def test_dispatch_uses_active_ticket_when_not_provided(dispatch_workspace: Path) -> None:
    stage_dispatch.dispatch_stage_command(
        "/skill:tasks-new",
        ticket="P4-2002",
        argv=["--force-template"],
        cwd=dispatch_workspace,
        check=True,
    )

    result = stage_dispatch.dispatch_stage_command(
        "/feature-dev-aidd:spec-interview",
        cwd=dispatch_workspace,
        check=True,
    )
    assert result.returncode == 0
    assert result.target.resolved_command == "spec-interview"
    assert result.ticket == "P4-2002"

    spec_path = dispatch_workspace / "aidd" / "docs" / "spec" / "P4-2002.spec.yaml"
    assert spec_path.exists()

    state = read_active_state(dispatch_workspace)
    assert state.ticket == "P4-2002"
    assert state.stage == "spec-interview"


def test_resolve_dispatch_target_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        stage_dispatch.resolve_dispatch_target("/skill:not-exist")


def test_dispatch_idea_research_plan_chain_regression(dispatch_workspace: Path) -> None:
    idea = stage_dispatch.dispatch_stage_command(
        "/skill:idea-new",
        ticket="P4-3003",
        cwd=dispatch_workspace,
        check=False,
    )
    assert idea.target.resolved_command == "idea-new"
    idea_state = read_active_state(dispatch_workspace)
    assert idea_state.ticket == "P4-3003"
    assert idea_state.stage == "idea"

    research = stage_dispatch.dispatch_stage_command(
        "/skill:researcher",
        ticket="P4-3003",
        argv=["--auto"],
        cwd=dispatch_workspace,
        check=False,
    )
    assert research.target.resolved_command == "researcher"
    research_output = f"{research.stdout}\n{research.stderr}"
    assert "cannot import name" not in research_output
    research_state = read_active_state(dispatch_workspace)
    assert research_state.stage == "research"

    plan = stage_dispatch.dispatch_stage_command(
        "/skill:plan-new",
        ticket="P4-3003",
        cwd=dispatch_workspace,
        check=False,
    )
    assert plan.target.resolved_command == "plan-new"
    plan_output = f"{plan.stdout}\n{plan.stderr}"
    assert "cannot import name" not in plan_output
    plan_state = read_active_state(dispatch_workspace)
    assert plan_state.stage == "plan"
