"""Tests for the aidd-init bootstrap CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "skills" / "aidd-init" / "runtime" / "init.py"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_run_init_generates_workspace(tmp_path) -> None:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()

    env = os.environ.copy()
    env.setdefault("AIDD_ROOT", str(PROJECT_ROOT))

    subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--force"],
        cwd=workspace_root,
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )

    project_root = workspace_root / "aidd"
    assert (project_root / "docs" / "prd" / "template.md").exists()
    assert (project_root / "docs" / "plan" / "template.md").exists()
    assert (project_root / "AGENTS.md").exists()

    settings_path = workspace_root / ".aidd" / "settings.json"
    assert settings_path.exists()
