from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from aidd_runtime import command_runner, readiness_gates
from aidd_runtime import diff_boundary_check as diff_boundary_check_module


class _Summary:
    def __init__(
        self,
        *,
        status: str | None,
        question_count: int = 0,
        path_count: int | None = None,
        age_days: int | None = None,
        skipped_reason: str | None = None,
    ) -> None:
        self.status = status
        self.question_count = question_count
        self.path_count = path_count
        self.age_days = age_days
        self.skipped_reason = skipped_reason


def test_run_analyst_gate_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = types.ModuleType("aidd_runtime.analyst_guard")

    class AnalystValidationError(RuntimeError):
        pass

    fake.AnalystValidationError = AnalystValidationError
    fake.load_settings = lambda root: {"enabled": True}  # noqa: E731
    fake.validate_prd = lambda *args, **kwargs: _Summary(
        status=None, question_count=0
    )  # noqa: E731
    monkeypatch.setitem(sys.modules, "aidd_runtime.analyst_guard", fake)

    skipped = readiness_gates.run_analyst_gate(tmp_path, ticket="T-1")
    assert skipped.skipped is True
    assert skipped.returncode == 0

    fake.validate_prd = lambda *args, **kwargs: _Summary(
        status="READY", question_count=3
    )  # noqa: E731
    ok = readiness_gates.run_analyst_gate(tmp_path, ticket="T-1")
    assert ok.returncode == 0
    assert "status: READY" in ok.output

    def _raise(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AnalystValidationError("invalid dialog")

    fake.validate_prd = _raise
    failed = readiness_gates.run_analyst_gate(tmp_path, ticket="T-1")
    assert failed.returncode == 2
    assert "invalid dialog" in failed.output


def test_run_research_gate_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = types.ModuleType("aidd_runtime.research_guard")

    class ResearchValidationError(RuntimeError):
        pass

    fake.ResearchValidationError = ResearchValidationError
    fake.load_settings = lambda root: {"enabled": True}  # noqa: E731
    fake.validate_research = lambda *args, **kwargs: _Summary(
        status=None, skipped_reason="pending-baseline"
    )  # noqa: E731
    monkeypatch.setitem(sys.modules, "aidd_runtime.research_guard", fake)

    pending = readiness_gates.run_research_gate(tmp_path, ticket="T-2")
    assert pending.skipped is True
    assert "pending-baseline" in pending.output

    fake.validate_research = lambda *args, **kwargs: _Summary(
        status=None, skipped_reason="disabled"
    )  # noqa: E731
    disabled = readiness_gates.run_research_gate(tmp_path, ticket="T-2")
    assert disabled.skipped is True
    assert "disabled" in disabled.output

    fake.validate_research = lambda *args, **kwargs: _Summary(  # noqa: E731
        status="READY",
        path_count=12,
        age_days=1,
    )
    ok = readiness_gates.run_research_gate(tmp_path, ticket="T-2")
    assert ok.returncode == 0
    assert "paths: 12" in ok.output
    assert "age: 1d" in ok.output

    def _raise(*args, **kwargs):  # noqa: ANN002, ANN003
        raise ResearchValidationError("missing rlm pack")

    fake.validate_research = _raise
    failed = readiness_gates.run_research_gate(tmp_path, ticket="T-2")
    assert failed.returncode == 2
    assert "missing rlm pack" in failed.output


def test_run_diff_boundary_check_branches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "aidd"
    root.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(readiness_gates.runtime, "read_active_work_item", lambda _root: "")
    no_item = readiness_gates.run_diff_boundary_check(root, ticket="T-3")
    assert no_item.skipped is True
    assert "no active work_item" in no_item.output

    monkeypatch.setattr(readiness_gates.runtime, "read_active_work_item", lambda _root: "I1")
    monkeypatch.setattr(
        readiness_gates.runtime, "resolve_scope_key", lambda *_args, **_kwargs: "I1"
    )
    missing_pack = readiness_gates.run_diff_boundary_check(root, ticket="T-3")
    assert missing_pack.skipped is True
    assert "loop pack missing" in missing_pack.output

    loop_pack = root / "reports" / "loops" / "T-3" / "I1.loop.pack.md"
    loop_pack.parent.mkdir(parents=True, exist_ok=True)
    loop_pack.write_text("pack", encoding="utf-8")

    def _main(args: list[str]) -> int:
        print("boundary-ok")
        assert "--allowed" in args
        return 0

    monkeypatch.setattr(diff_boundary_check_module, "main", _main)

    ok = readiness_gates.run_diff_boundary_check(root, ticket="T-3", allowed="src/**")
    assert ok.returncode == 0
    assert "boundary-ok" in ok.output


def test_run_qa_gate_and_stage_preflight(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    qa_script = plugin_root / "skills" / "qa" / "runtime" / "qa.py"
    qa_script.parent.mkdir(parents=True, exist_ok=True)
    qa_script.write_text("print('qa')\n", encoding="utf-8")

    root = tmp_path / "workspace" / "aidd"
    root.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(readiness_gates.runtime, "require_plugin_root", lambda: plugin_root)
    monkeypatch.setattr(
        readiness_gates.command_runner,
        "build_runtime_env",
        lambda _plugin_root: {"AIDD_ROOT": str(plugin_root)},
    )

    captured: dict[str, object] = {}

    def _fake_run_python(script_path, **kwargs):  # noqa: ANN001
        captured["script_path"] = script_path
        captured["cwd"] = kwargs["cwd"]
        captured["argv"] = kwargs["argv"]
        return command_runner.CommandResult(
            command=("python", str(script_path)),
            cwd=kwargs["cwd"],
            returncode=0,
            stdout="qa-ok",
            stderr="",
        )

    monkeypatch.setattr(readiness_gates.command_runner, "run_python", _fake_run_python)

    qa_result = readiness_gates.run_qa_gate(
        root,
        ticket="T-4",
        slug_hint="slug-4",
        branch="feature/demo",
        extra_argv=["--skip-tests"],
    )
    assert qa_result.returncode == 0
    assert "qa-ok" in qa_result.output
    assert captured["script_path"] == qa_script
    assert captured["cwd"] == root.parent
    assert "--gate" in captured["argv"]

    calls: list[str] = []

    def _ok(name: str):
        def _run(*args, **kwargs):  # noqa: ANN002, ANN003
            calls.append(name)
            return readiness_gates.GateResult(name=name, returncode=0, output="ok")

        return _run

    monkeypatch.setattr(readiness_gates, "run_analyst_gate", _ok("analyst"))
    monkeypatch.setattr(readiness_gates, "run_plan_review_gate", _ok("plan"))
    monkeypatch.setattr(readiness_gates, "run_prd_review_gate", _ok("prd"))
    monkeypatch.setattr(readiness_gates, "run_research_gate", _ok("research"))
    monkeypatch.setattr(readiness_gates, "run_tasklist_check", _ok("tasklist"))

    def _diff(*args, **kwargs):  # noqa: ANN002, ANN003
        calls.append("diff")
        return readiness_gates.GateResult(name="diff", returncode=0, output="ok")

    monkeypatch.setattr(readiness_gates, "run_diff_boundary_check", _diff)

    qa_preflight = readiness_gates.run_stage_preflight(root, ticket="T-4", stage="qa")
    assert qa_preflight.returncode == 0
    assert calls == ["analyst", "plan", "prd", "research", "tasklist"]

    noop = readiness_gates.run_stage_preflight(root, ticket="T-4", stage="idea")
    assert noop.name == "preflight"
    assert noop.output == ""


def test_capture_and_join_helpers() -> None:
    status, output = readiness_gates._run_with_capture(lambda: 0)
    assert status == 0
    assert output == ""

    def _raise() -> int:
        raise ValueError("boom")

    failed_status, failed_output = readiness_gates._run_with_capture(_raise)
    assert failed_status == 2
    assert "boom" in failed_output

    assert readiness_gates._join_output("out", "err") == "out\nerr"
    assert readiness_gates._join_output("", "err") == "err"
