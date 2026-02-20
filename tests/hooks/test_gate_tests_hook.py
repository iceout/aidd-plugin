from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.hooks.hook_loader import load_hook_module


@pytest.fixture()
def gate_tests_module():
    return load_hook_module("hook_gate_tests", "hooks/gate-tests.sh")


def test_bootstrap_requires_aidd_root(
    gate_tests_module,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("AIDD_ROOT", raising=False)
    with pytest.raises(SystemExit) as exc:
        gate_tests_module._bootstrap()
    assert exc.value.code == 2
    assert "AIDD_ROOT is required" in capsys.readouterr().err


def test_main_returns_2_when_format_hook_missing(
    gate_tests_module,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plugin_root = tmp_path / "plugin"
    plugin_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AIDD_ROOT", str(plugin_root))

    code = gate_tests_module.main()
    assert code == 2
    assert "missing hook" in capsys.readouterr().err


def test_main_invokes_format_hook_and_propagates_return_code(
    gate_tests_module,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plugin_root = tmp_path / "plugin"
    script = plugin_root / "hooks" / "format-and-test.sh"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    monkeypatch.setenv("AIDD_ROOT", str(plugin_root))

    captured: dict[str, object] = {}

    def _fake_run(command, **kwargs):  # noqa: ANN001
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(gate_tests_module.subprocess, "run", _fake_run)

    code = gate_tests_module.main()
    assert code == 7
    assert captured["command"] == [gate_tests_module.sys.executable, str(script)]
    assert captured["kwargs"]["check"] is False
