"""Smoke tests for the post-migration runtime layout."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INIT_SCRIPT = PROJECT_ROOT / "skills" / "aidd-init" / "runtime" / "init.py"
RLM_TARGETS_SCRIPT = PROJECT_ROOT / "skills" / "aidd-core" / "runtime" / "rlm_targets.py"
RESEARCH_SCRIPT = PROJECT_ROOT / "skills" / "researcher" / "runtime" / "research.py"
QA_SCRIPT = PROJECT_ROOT / "skills" / "qa" / "runtime" / "qa.py"
HOOK_SCRIPT = PROJECT_ROOT / "hooks" / "gate-workflow.sh"

SMOKE_TICKET = "P13-SMOKE-001"


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


@pytest.fixture(scope="module")
def smoke_workspace(tmp_path_factory: pytest.TempPathFactory) -> Path:
    workspace_root = tmp_path_factory.mktemp("aidd-layout-smoke")
    env = os.environ.copy()
    env["AIDD_ROOT"] = str(PROJECT_ROOT)
    init_proc = _run([sys.executable, str(INIT_SCRIPT), "--force"], cwd=workspace_root, env=env)
    assert init_proc.returncode == 0, init_proc.stderr or init_proc.stdout
    assert (workspace_root / "aidd" / "docs" / "prd" / "template.md").exists()
    return workspace_root


def test_rlm_targets_smoke_blocks_on_missing_hints(smoke_workspace: Path) -> None:
    env = os.environ.copy()
    env["AIDD_ROOT"] = str(PROJECT_ROOT)
    proc = _run(
        [sys.executable, str(RLM_TARGETS_SCRIPT), "--ticket", SMOKE_TICKET],
        cwd=smoke_workspace,
        env=env,
    )
    output = f"{proc.stdout}\n{proc.stderr}"
    assert proc.returncode != 0
    assert "AIDD:RESEARCH_HINTS" in output
    assert "cannot import name" not in output


def test_research_smoke_blocks_on_missing_hints(smoke_workspace: Path) -> None:
    env = os.environ.copy()
    env["AIDD_ROOT"] = str(PROJECT_ROOT)
    proc = _run(
        [sys.executable, str(RESEARCH_SCRIPT), "--ticket", SMOKE_TICKET, "--auto"],
        cwd=smoke_workspace,
        env=env,
    )
    output = f"{proc.stdout}\n{proc.stderr}"
    assert proc.returncode != 0
    assert "AIDD:RESEARCH_HINTS" in output
    assert "cannot import name" not in output


def test_qa_smoke_skip_tests(smoke_workspace: Path) -> None:
    env = os.environ.copy()
    env["AIDD_ROOT"] = str(PROJECT_ROOT)
    proc = _run(
        [sys.executable, str(QA_SCRIPT), "--ticket", SMOKE_TICKET, "--skip-tests"],
        cwd=smoke_workspace,
        env=env,
    )
    output = f"{proc.stdout}\n{proc.stderr}"
    assert proc.returncode == 0, output
    assert "tests_summary" in output and "skipped" in output
    assert "cannot import name" not in output


def test_hook_smoke_runs_with_new_layout(smoke_workspace: Path) -> None:
    env = os.environ.copy()
    env["AIDD_ROOT"] = str(PROJECT_ROOT)
    proc = _run([sys.executable, str(HOOK_SCRIPT)], cwd=smoke_workspace, env=env)
    output = f"{proc.stdout}\n{proc.stderr}"
    assert proc.returncode == 0, output
    assert "cannot import name" not in output
