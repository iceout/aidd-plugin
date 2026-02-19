from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from aidd_runtime import command_runner


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_build_runtime_env_sets_aidd_root() -> None:
    env = command_runner.build_runtime_env(PROJECT_ROOT, base_env={"FOO": "bar"})
    assert env["AIDD_ROOT"] == str(PROJECT_ROOT)
    assert env["FOO"] == "bar"


def test_run_command_success() -> None:
    result = command_runner.run_command(
        [sys.executable, "-c", "print('ok')"],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
    )
    assert result.ok is True
    assert result.returncode == 0
    assert result.stdout.strip() == "ok"


def test_run_command_check_raises_on_failure() -> None:
    with pytest.raises(RuntimeError, match="failed sample"):
        command_runner.run_command(
            [sys.executable, "-c", "import sys; sys.stderr.write('boom'); sys.exit(3)"],
            cwd=PROJECT_ROOT,
            env=os.environ.copy(),
            check=True,
            error_context="failed sample",
        )

