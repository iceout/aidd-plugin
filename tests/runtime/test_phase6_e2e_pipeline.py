from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INIT_SCRIPT = PROJECT_ROOT / "skills" / "aidd-init" / "runtime" / "init.py"
SET_ACTIVE_FEATURE_SCRIPT = (
    PROJECT_ROOT / "skills" / "aidd-flow-state" / "runtime" / "set_active_feature.py"
)
SET_ACTIVE_STAGE_SCRIPT = (
    PROJECT_ROOT / "skills" / "aidd-flow-state" / "runtime" / "set_active_stage.py"
)
IDEA_SCRIPT = PROJECT_ROOT / "skills" / "idea-new" / "runtime" / "analyst_check.py"
RESEARCH_SCRIPT = PROJECT_ROOT / "skills" / "researcher" / "runtime" / "research.py"
PLAN_SCRIPT = PROJECT_ROOT / "skills" / "plan-new" / "runtime" / "research_check.py"
TASKS_SCRIPT = PROJECT_ROOT / "skills" / "tasks-new" / "runtime" / "tasks_new.py"


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


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


def _write_prd_with_hints(workspace: Path, ticket: str) -> None:
    prd_path = workspace / "aidd" / "docs" / "prd" / f"{ticket}.prd.md"
    prd_path.write_text(
        (
            f"# PRD — {ticket}\n\n"
            "Status: READY\n"
            f"Ticket: {ticket}\n\n"
            "## Dialog analyst\n"
            f"Research reference: `aidd/docs/research/{ticket}.md`\n"
            "Question 1: scope?\n"
            "Answer 1: keep minimal\n\n"
            "## AIDD:ANSWERS\n"
            "- Answer 1: keep minimal\n\n"
            "## AIDD:RESEARCH_HINTS\n"
            "- Paths: docs,config\n"
            "- Keywords: aidd,flow\n"
            "- Notes: e2e phase6 pipeline\n"
        ),
        encoding="utf-8",
    )


@pytest.fixture()
def e2e_workspace(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["AIDD_ROOT"] = str(PROJECT_ROOT)

    init = _run([sys.executable, str(INIT_SCRIPT), "--force"], cwd=workspace, env=env)
    assert init.returncode == 0, init.stderr or init.stdout
    _configure_relaxed_gates(workspace)
    return workspace, env


def test_e2e_workspace_init_idea_research_plan_tasklist_pipeline(
    e2e_workspace: tuple[Path, dict[str, str]],
) -> None:
    workspace, env = e2e_workspace
    ticket = "P6-E2E-1001"

    set_feature = _run(
        [sys.executable, str(SET_ACTIVE_FEATURE_SCRIPT), ticket, "--skip-prd-scaffold"],
        cwd=workspace / "aidd",
        env=env,
    )
    assert set_feature.returncode == 0, set_feature.stderr or set_feature.stdout

    _write_prd_with_hints(workspace, ticket)

    set_stage_idea = _run(
        [sys.executable, str(SET_ACTIVE_STAGE_SCRIPT), "idea"],
        cwd=workspace / "aidd",
        env=env,
    )
    assert set_stage_idea.returncode == 0, set_stage_idea.stderr or set_stage_idea.stdout

    idea = _run(
        [sys.executable, str(IDEA_SCRIPT), "--ticket", ticket],
        cwd=workspace,
        env=env,
    )
    assert idea.returncode == 0, idea.stderr or idea.stdout

    set_stage_research = _run(
        [sys.executable, str(SET_ACTIVE_STAGE_SCRIPT), "research"],
        cwd=workspace / "aidd",
        env=env,
    )
    assert set_stage_research.returncode == 0, (
        set_stage_research.stderr or set_stage_research.stdout
    )

    research = _run(
        [sys.executable, str(RESEARCH_SCRIPT), "--ticket", ticket, "--auto"],
        cwd=workspace,
        env=env,
    )
    assert research.returncode == 0, research.stderr or research.stdout

    set_stage_plan = _run(
        [sys.executable, str(SET_ACTIVE_STAGE_SCRIPT), "plan"],
        cwd=workspace / "aidd",
        env=env,
    )
    assert set_stage_plan.returncode == 0, set_stage_plan.stderr or set_stage_plan.stdout

    plan = _run(
        [sys.executable, str(PLAN_SCRIPT), "--ticket", ticket],
        cwd=workspace,
        env=env,
    )
    assert plan.returncode == 0, plan.stderr or plan.stdout

    tasks = _run(
        [sys.executable, str(TASKS_SCRIPT), "--ticket", ticket, "--force-template"],
        cwd=workspace,
        env=env,
    )
    assert tasks.returncode == 0, tasks.stderr or tasks.stdout

    aidd_dir = workspace / "aidd"
    assert (aidd_dir / "docs" / "prd" / f"{ticket}.prd.md").exists()
    assert (aidd_dir / "docs" / "plan" / f"{ticket}.md").exists()
    assert (aidd_dir / "docs" / "tasklist" / f"{ticket}.md").exists()

    pack_candidates = [
        aidd_dir / "reports" / "research" / f"{ticket}-rlm.pack.json",
        aidd_dir / "reports" / "research" / f"{ticket}-rlm.worklist.pack.json",
    ]
    assert any(path.exists() for path in pack_candidates)
