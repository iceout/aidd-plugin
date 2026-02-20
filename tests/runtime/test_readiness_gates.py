from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from aidd_runtime import readiness_gates, stage_dispatch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INIT_SCRIPT = PROJECT_ROOT / "skills" / "aidd-init" / "runtime" / "init.py"


@pytest.fixture()
def workflow_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["AIDD_ROOT"] = str(PROJECT_ROOT)
    proc = subprocess.run(
        [sys.executable, str(INIT_SCRIPT), "--force"],
        cwd=workspace,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return workspace


def test_run_stage_preflight_stops_on_first_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[str] = []

    def _ok(name: str):
        def _run(*args, **kwargs):  # noqa: ANN002, ANN003
            calls.append(name)
            return readiness_gates.GateResult(name=name, returncode=0, output=f"{name} ok")

        return _run

    def _fail(*args, **kwargs):  # noqa: ANN002, ANN003
        calls.append("plan_review_gate")
        return readiness_gates.GateResult(
            name="plan_review_gate",
            returncode=2,
            output="BLOCK: plan review failed",
        )

    monkeypatch.setattr(readiness_gates, "run_analyst_gate", _ok("analyst_check"))
    monkeypatch.setattr(readiness_gates, "run_plan_review_gate", _fail)
    monkeypatch.setattr(readiness_gates, "run_prd_review_gate", _ok("prd_review_gate"))
    monkeypatch.setattr(readiness_gates, "run_research_gate", _ok("research_check"))
    monkeypatch.setattr(readiness_gates, "run_tasklist_check", _ok("tasklist_check"))
    monkeypatch.setattr(readiness_gates, "run_diff_boundary_check", _ok("diff_boundary_check"))

    result = readiness_gates.run_stage_preflight(
        tmp_path,
        ticket="P5-FAIL-001",
        stage="implement",
        branch="feature/p5",
    )

    assert result.returncode == 2
    assert result.name == "plan_review_gate"
    assert calls == ["analyst_check", "plan_review_gate"]


def test_dispatch_implement_blocked_by_preflight(
    monkeypatch: pytest.MonkeyPatch,
    workflow_workspace: Path,
) -> None:
    def _fail_preflight(*args, **kwargs):  # noqa: ANN002, ANN003
        return readiness_gates.GateResult(
            name="tasklist_check",
            returncode=2,
            output="BLOCK: tasklist check failed from preflight",
        )

    monkeypatch.setenv("AIDD_STAGE_DISPATCH_GATES", "1")
    monkeypatch.setattr(stage_dispatch.readiness_gates, "run_stage_preflight", _fail_preflight)

    result = stage_dispatch.dispatch_stage_command(
        "/skill:implement",
        ticket="P5-BLOCK-002",
        cwd=workflow_workspace,
        check=False,
    )

    assert result.returncode == 2
    assert "BLOCK: tasklist check failed from preflight" in result.stderr
    assert result.command == ()


def test_dispatch_qa_entrypoint_uses_shared_gate_wrapper() -> None:
    target = stage_dispatch.resolve_dispatch_target("/skill:qa")
    assert target.spec.entrypoint == "skills/aidd-core/runtime/qa_gate.py"
