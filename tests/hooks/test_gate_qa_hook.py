from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from hooks import hooklib
from tests.hooks.hook_loader import load_hook_module


@pytest.fixture()
def gate_qa_module():
    return load_hook_module("hook_gate_qa", "hooks/gate-qa.sh")


def test_bootstrap_requires_aidd_root(
    gate_qa_module,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("AIDD_ROOT", raising=False)
    with pytest.raises(SystemExit) as exc:
        gate_qa_module._bootstrap()
    assert exc.value.code == 2
    assert "AIDD_ROOT is required" in capsys.readouterr().err


def test_main_invokes_qa_gate_with_workspace_context(
    gate_qa_module,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin_root = tmp_path / "plugin"
    qa_runtime = plugin_root / "skills" / "aidd-core" / "runtime" / "qa_gate.py"
    qa_runtime.parent.mkdir(parents=True, exist_ok=True)
    qa_runtime.write_text("print('qa gate')\n", encoding="utf-8")

    workspace = tmp_path / "workspace" / "aidd"
    workspace.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("AIDD_ROOT", str(plugin_root))

    ctx = hooklib.HookContext(
        hook_event_name="Stop",
        session_id="s-1",
        transcript_path=None,
        cwd=str(workspace),
        permission_mode=None,
        raw={},
    )
    monkeypatch.setattr(hooklib, "read_hook_context", lambda: ctx)
    monkeypatch.setattr(hooklib, "resolve_project_root", lambda _ctx: (workspace, False))

    captured: dict[str, object] = {}

    def _fake_run(command, **kwargs):  # noqa: ANN001
        captured["command"] = command
        captured["cwd"] = kwargs.get("cwd")
        captured["check"] = kwargs.get("check")
        return SimpleNamespace(returncode=3)

    monkeypatch.setattr(gate_qa_module.subprocess, "run", _fake_run)

    code = gate_qa_module.main(["--skip-tests"])
    assert code == 3
    assert captured["command"] == [
        gate_qa_module.sys.executable,
        str(qa_runtime),
        "--skip-tests",
    ]
    assert captured["cwd"] == workspace
    assert captured["check"] is False
