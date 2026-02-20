from __future__ import annotations

from pathlib import Path

from hooks import hooklib


def test_payload_file_path_prefers_tool_input() -> None:
    payload = {
        "tool_input": {
            "file_path": "src/main.py",
        },
        "file_path": "fallback.py",
    }
    assert hooklib.payload_file_path(payload) == "src/main.py"


def test_resolve_hooks_mode_defaults_to_fast(monkeypatch) -> None:
    monkeypatch.delenv("AIDD_HOOKS_MODE", raising=False)
    assert hooklib.resolve_hooks_mode() == "fast"
    monkeypatch.setenv("AIDD_HOOKS_MODE", "strict")
    assert hooklib.resolve_hooks_mode() == "strict"
    monkeypatch.setenv("AIDD_HOOKS_MODE", "unsupported")
    assert hooklib.resolve_hooks_mode() == "fast"


def test_resolve_project_root_prefers_aidd_child(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "aidd" / "docs").mkdir(parents=True, exist_ok=True)
    (workspace / "aidd" / "hooks").mkdir(parents=True, exist_ok=True)

    resolved, used_workspace = hooklib.resolve_project_root(cwd=str(workspace))
    assert resolved == (workspace / "aidd").resolve()
    assert used_workspace is True
