from __future__ import annotations

from pathlib import Path

from aidd_runtime import qa as qa_runtime
from aidd_runtime import tasklist_parser


def test_parse_test_execution_splits_scalar_chained_tasks() -> None:
    payload = tasklist_parser.parse_test_execution(
        [
            "- profile: targeted",
            "- tasks: `ruff check bandeng/tools/service.py tests/test_service.py && dae docker shell -s app -c \"sh -lc 'python -m pytest -q --noconftest tests/test_service.py'\"`",
            "- filters: --noconftest",
            "- when: checkpoint",
            "- reason: speed",
        ]
    )

    assert payload["tasks"] == [
        "ruff check bandeng/tools/service.py tests/test_service.py",
        "dae docker shell -s app -c \"sh -lc 'python -m pytest -q --noconftest tests/test_service.py'\"",
    ]
    assert payload["cwd"] == ""


def test_parse_test_execution_keeps_quoted_shell_ops_and_strips_ticks() -> None:
    payload = tasklist_parser.parse_test_execution(
        [
            "- profile: targeted",
            "- tasks:",
            '  - sh -lc "python -m pytest -q tests/test_a.py && echo done"',
            "  - `ruff check bandeng/tools/service.py`",
            "- cwd: repo_root",
        ]
    )
    assert payload["tasks"] == [
        'sh -lc "python -m pytest -q tests/test_a.py && echo done"',
        "ruff check bandeng/tools/service.py",
    ]
    assert payload["cwd"] == "repo_root"


def test_qa_commands_from_tasks_strips_wrapping_ticks() -> None:
    commands = qa_runtime._commands_from_tasks(
        ["`ruff check bandeng/tools/service.py tests/test_service.py`"]
    )
    assert commands == [["ruff", "check", "bandeng/tools/service.py", "tests/test_service.py"]]


def test_resolve_tasklist_cwd_supports_repo_root_and_aidd(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    target = workspace / "aidd"
    target.mkdir(parents=True)

    assert (
        qa_runtime._resolve_tasklist_cwd("", target_root=target, workspace_root=workspace)
        == workspace
    )
    assert (
        qa_runtime._resolve_tasklist_cwd("repo_root", target_root=target, workspace_root=workspace)
        == workspace
    )
    assert (
        qa_runtime._resolve_tasklist_cwd("aidd", target_root=target, workspace_root=workspace)
        == target
    )

    tests_dir = workspace / "tests"
    tests_dir.mkdir()
    assert (
        qa_runtime._resolve_tasklist_cwd("tests", target_root=target, workspace_root=workspace)
        == tests_dir
    )
