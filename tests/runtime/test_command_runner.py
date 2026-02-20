from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from aidd_runtime import command_runner, ide_profiles

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_build_runtime_env_sets_aidd_root() -> None:
    env = command_runner.build_runtime_env(PROJECT_ROOT, base_env={"FOO": "bar"})
    assert env["AIDD_ROOT"] == str(PROJECT_ROOT)
    assert env["FOO"] == "bar"
    assert env["AIDD_IDE_PROFILE"] == "kimi"
    assert "AIDD_SKILLS_DIRS" in env
    assert env["AIDD_PRIMARY_SKILLS_DIR"]


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


def test_build_runtime_env_with_explicit_profile() -> None:
    env = command_runner.build_runtime_env(PROJECT_ROOT, profile="codex", base_env={})
    assert env["AIDD_IDE_PROFILE"] == "codex"
    assert env["AIDD_HOST"] == "codex"
    assert ".codex/skills" in env["AIDD_SKILLS_DIRS"]


def test_build_runtime_env_with_explicit_skills_dirs_override() -> None:
    custom = f"/tmp/a{os.pathsep}/tmp/b"
    env = command_runner.build_runtime_env(
        PROJECT_ROOT,
        profile="cursor",
        base_env={"AIDD_SKILLS_DIRS": custom},
    )
    assert env["AIDD_SKILLS_DIRS"] == custom
    assert env["AIDD_PRIMARY_SKILLS_DIR"] == "/tmp/a"


def test_run_command_timeout() -> None:
    result = command_runner.run_command(
        [sys.executable, "-c", "import time; time.sleep(0.2)"],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
        timeout_sec=0.05,
    )
    assert result.returncode == 124
    assert result.timed_out is True
    assert "timed out" in result.stderr


def test_run_command_output_truncation() -> None:
    result = command_runner.run_command(
        [sys.executable, "-c", "print('x' * 5000)"],
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
        max_stdout_bytes=128,
    )
    assert result.returncode == 0
    assert result.stdout_truncated is True
    assert "output truncated to 128 bytes" in result.stdout


def test_ide_profile_resolution() -> None:
    profile = ide_profiles.resolve_profile("cursor")
    assert profile.name == "cursor"
