from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from aidd_runtime import stage_dispatch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INIT_SCRIPT = PROJECT_ROOT / "skills" / "aidd-init" / "runtime" / "init.py"


def _run_init(workspace: Path) -> None:
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


def _read_active_payload(workspace: Path) -> dict[str, object]:
    active_path = workspace / "aidd" / "docs" / ".active.json"
    return json.loads(active_path.read_text(encoding="utf-8"))


def _configure_relaxed_gates(workspace: Path) -> None:
    gates_path = workspace / "aidd" / "config" / "gates.json"
    payload = json.loads(gates_path.read_text(encoding="utf-8"))
    payload["analyst"] = {
        "enabled": False,
    }
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


def _write_prd_with_research_hints(workspace: Path, ticket: str) -> None:
    prd_path = workspace / "aidd" / "docs" / "prd" / f"{ticket}.prd.md"
    prd_path.parent.mkdir(parents=True, exist_ok=True)
    prd_path.write_text(
        (
            f"# PRD — {ticket}\n\n"
            "Status: READY\n"
            f"Ticket: {ticket}\n\n"
            "## Dialog analyst\n"
            f"Research reference: `aidd/docs/research/{ticket}.md`\n"
            "Question 1: minimal question\n"
            "Answer 1: minimal answer\n\n"
            "## AIDD:ANSWERS\n"
            "- Answer 1: minimal answer\n\n"
            "## AIDD:RESEARCH_HINTS\n"
            "- Paths: docs,config\n"
            "- Keywords: stage,dispatch\n"
            "- Notes: integration test fixture\n"
        ),
        encoding="utf-8",
    )


@pytest.fixture()
def orchestration_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _run_init(workspace)
    _configure_relaxed_gates(workspace)
    return workspace


def test_stage_orchestration_chain_generates_artifacts(orchestration_workspace: Path) -> None:
    ticket = "P4-CHAIN-1001"

    idea = stage_dispatch.dispatch_stage_command(
        "/skill:idea-new",
        ticket=ticket,
        cwd=orchestration_workspace,
        check=True,
    )
    assert idea.returncode == 0
    assert idea.target.resolved_command == "idea-new"
    assert _read_active_payload(orchestration_workspace)["stage"] == "idea"

    _write_prd_with_research_hints(orchestration_workspace, ticket)

    research = stage_dispatch.dispatch_stage_command(
        "/skill:researcher",
        ticket=ticket,
        argv=["--auto"],
        cwd=orchestration_workspace,
        check=True,
    )
    assert research.returncode == 0
    assert research.target.resolved_command == "researcher"
    assert _read_active_payload(orchestration_workspace)["stage"] == "research"

    aidd_root = orchestration_workspace / "aidd"
    assert (aidd_root / "docs" / "research" / f"{ticket}.md").exists()
    assert (aidd_root / "reports" / "research" / f"{ticket}-rlm-targets.json").exists()
    assert (aidd_root / "reports" / "research" / f"{ticket}-rlm-manifest.json").exists()
    assert (aidd_root / "reports" / "research" / f"{ticket}-rlm.worklist.pack.json").exists()

    plan = stage_dispatch.dispatch_stage_command(
        "/skill:plan-new",
        ticket=ticket,
        cwd=orchestration_workspace,
        check=True,
    )
    assert plan.returncode == 0
    assert plan.target.resolved_command == "plan-new"
    assert _read_active_payload(orchestration_workspace)["stage"] == "plan"

    tasks = stage_dispatch.dispatch_stage_command(
        "/skill:tasks-new",
        ticket=ticket,
        argv=["--force-template"],
        cwd=orchestration_workspace,
        check=True,
    )
    assert tasks.returncode == 0
    assert tasks.target.resolved_command == "tasks-new"

    active_payload = _read_active_payload(orchestration_workspace)
    assert active_payload["ticket"] == ticket
    assert active_payload["stage"] == "tasklist"
    assert (aidd_root / "docs" / "tasklist" / f"{ticket}.md").exists()


def test_legacy_flow_alias_orchestration_chain(orchestration_workspace: Path) -> None:
    ticket = "P4-ALIAS-2002"
    _write_prd_with_research_hints(orchestration_workspace, ticket)

    idea = stage_dispatch.dispatch_stage_command(
        "/flow:aidd-idea-flow",
        ticket=ticket,
        cwd=orchestration_workspace,
        check=True,
    )
    assert idea.returncode == 0
    assert idea.target.is_legacy_alias is True
    assert idea.target.resolved_command == "idea-new"
    assert _read_active_payload(orchestration_workspace)["stage"] == "idea"

    research = stage_dispatch.dispatch_stage_command(
        "/flow:aidd-research-flow",
        ticket=ticket,
        argv=["--auto"],
        cwd=orchestration_workspace,
        check=True,
    )
    assert research.returncode == 0
    assert research.target.is_legacy_alias is True
    assert research.target.resolved_command == "researcher"
    assert _read_active_payload(orchestration_workspace)["stage"] == "research"

    plan = stage_dispatch.dispatch_stage_command(
        "/flow:aidd-plan-flow",
        ticket=ticket,
        cwd=orchestration_workspace,
        check=True,
    )
    assert plan.returncode == 0
    assert plan.target.is_legacy_alias is True
    assert plan.target.resolved_command == "plan-new"

    active_payload = _read_active_payload(orchestration_workspace)
    assert active_payload["ticket"] == ticket
    assert active_payload["stage"] == "plan"
