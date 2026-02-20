from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.hooks.hook_loader import load_hook_module


@pytest.fixture()
def format_hook_module():
    return load_hook_module("hook_format_and_test", "hooks/format-and-test.sh")


def test_detect_workspace_root_from_aidd_subdir(format_hook_module, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    aidd_dir = workspace / "aidd"
    (aidd_dir / "docs").mkdir(parents=True, exist_ok=True)

    assert format_hook_module._detect_workspace_root(aidd_dir) == workspace
    assert format_hook_module._detect_workspace_root(workspace) == workspace


def test_build_candidates_order(
    format_hook_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts" / "test.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    (tmp_path / "Makefile").write_text("test:\n\t@echo ok\n", encoding="utf-8")
    (tmp_path / "tests").mkdir(parents=True, exist_ok=True)
    (tmp_path / "package.json").write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(
        format_hook_module.shutil,
        "which",
        lambda cmd: {"make": "/usr/bin/make", "npm": "/usr/bin/npm"}.get(cmd),
    )
    monkeypatch.setattr(format_hook_module, "_pytest_available", lambda: True)

    candidates = format_hook_module._build_candidates(tmp_path)
    assert candidates[0] == ["bash", "scripts/test.sh"]
    assert ["make", "test"] in candidates
    assert [format_hook_module.sys.executable, "-m", "pytest"] in candidates
    assert ["npm", "test"] in candidates


def test_run_command_missing_executable_returns_success(
    format_hook_module,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise(*args, **kwargs):  # noqa: ANN002, ANN003
        raise FileNotFoundError("missing")

    monkeypatch.setattr(format_hook_module.subprocess, "run", _raise)
    code = format_hook_module._run_command(["nope"], tmp_path)
    assert code == 0


def test_main_returns_zero_when_no_candidates(
    format_hook_module,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(format_hook_module, "_build_candidates", lambda _root: [])

    assert format_hook_module.main() == 0


def test_main_runs_first_candidate_only(
    format_hook_module,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    calls: list[tuple[list[str], Path]] = []

    monkeypatch.setattr(
        format_hook_module,
        "_build_candidates",
        lambda _root: [["cmd1", "a"], ["cmd2", "b"]],
    )

    def _fake_run(cmd: list[str], cwd: Path) -> int:
        calls.append((cmd, cwd))
        return 11

    monkeypatch.setattr(format_hook_module, "_run_command", _fake_run)

    code = format_hook_module.main()
    assert code == 11
    assert calls == [(["cmd1", "a"], tmp_path)]


def test_python_tests_present_by_pyproject_marker(format_hook_module, tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.pytest.ini_options]\naddopts='-q'\n", encoding="utf-8")
    assert format_hook_module._python_tests_present(tmp_path) is True

    pyproject.write_text("[project]\nname='demo'\n", encoding="utf-8")
    assert format_hook_module._python_tests_present(tmp_path) is False
