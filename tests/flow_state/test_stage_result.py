from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from aidd_runtime import stage_result


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_stage_result_helper_functions(tmp_path: Path) -> None:
    assert stage_result._split_items([" a,b ", " c "]) == ["a", "b", "c"]
    assert stage_result._dedupe(["x", "x", " y "]) == ["x", " y "]

    links = stage_result._parse_evidence_links(["tests=aidd/reports/tests.json", "extra", "extra"])
    assert links["tests"] == "aidd/reports/tests.json"
    assert links["links"] == ["extra"]

    stage_result._append_misc_link(links, "another")
    assert "another" in links["links"]
    assert stage_result._normalize_work_item_key("id=iteration_id_I7") == "iteration_id=I7"
    assert stage_result._normalize_work_item_key("id=H1") == "id=H1"

    log_dir = tmp_path / "reports" / "loops" / "TK-1"
    _write(log_dir / "cli.loop-001.stream.log", "x")
    _write(log_dir / "cli.loop-002.stream.log", "x")
    jsonl = log_dir / "cli.loop-002.stream.jsonl"
    _write(jsonl, "{}\n")
    latest = stage_result._latest_stream_log(tmp_path, "TK-1")
    assert latest is not None and latest.name == "cli.loop-002.stream.log"
    assert stage_result._stream_jsonl_for(latest) == jsonl


def test_reviewer_requirements_and_tests_policy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "aidd"
    target.mkdir()
    marker = target / "reports" / "reviewer" / "TK-1" / "scope.tests.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('{"tests":"required"}', encoding="utf-8")

    monkeypatch.setattr(
        stage_result.runtime,
        "load_gates_config",
        lambda _target: {
            "tests_required": "soft",
            "reviewer": {
                "enabled": True,
                "tests_marker": "aidd/reports/reviewer/{ticket}/{scope_key}.tests.json",
            },
        },
    )
    monkeypatch.setattr(stage_result.runtime, "reviewer_marker_path", lambda *_a, **_k: marker)
    monkeypatch.setattr(
        stage_result.gates, "resolve_stage_tests_policy", lambda _cfg, _stage: "targeted"
    )

    require, block, source = stage_result._tests_policy(
        target,
        ticket="TK-1",
        slug_hint="tk-1",
        scope_key="scope",
        stage="review",
    )
    assert (require, block) == (True, True)
    assert source.endswith("scope.tests.json")

    marker.write_text('{"tests":"optional"}', encoding="utf-8")
    require2, block2, _ = stage_result._tests_policy(
        target,
        ticket="TK-1",
        slug_hint="tk-1",
        scope_key="scope",
        stage="review",
    )
    assert (require2, block2) == (False, False)


def test_resolve_tests_evidence_prefers_pass_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from aidd_runtime.reports import tests_log

    target = tmp_path / "aidd"
    target.mkdir()
    pass_log = target / "reports" / "tests" / "pass.jsonl"
    pass_log.parent.mkdir(parents=True, exist_ok=True)
    pass_log.write_text("{}", encoding="utf-8")

    calls: list[tuple[tuple[str, ...], tuple[str, ...] | None]] = []

    def fake_latest_entry(
        _target: Path,
        _ticket: str,
        _scope_key: str,
        *,
        stages: list[str],
        statuses: tuple[str, ...] | None,
    ) -> tuple[dict | None, Path | None]:
        calls.append((tuple(stages), statuses))
        if statuses == ("pass", "fail"):
            return {"status": "pass"}, pass_log
        return None, None

    monkeypatch.setattr(tests_log, "latest_entry", fake_latest_entry)
    rel_path, has_evidence, entry = stage_result._resolve_tests_evidence(
        target,
        ticket="TK-1",
        scope_key="scope",
        stage="review",
    )
    assert has_evidence is True
    assert rel_path == "aidd/reports/tests/pass.jsonl"
    assert entry == {"status": "pass"}
    assert calls[0][0] == ("review", "implement")


def _mock_runtime_context(
    monkeypatch: pytest.MonkeyPatch,
    target: Path,
    *,
    default_ticket: str,
    scope_key: str = "scope",
) -> None:
    workspace = target.parent
    monkeypatch.setattr(stage_result.runtime, "require_workflow_root", lambda: (workspace, target))

    def _require_ticket(
        _target: Path, *, ticket: str | None = None, slug_hint: str | None = None
    ) -> tuple[str, SimpleNamespace]:
        resolved = ticket or default_ticket
        return resolved, SimpleNamespace(slug_hint=slug_hint or resolved.lower())

    monkeypatch.setattr(stage_result.runtime, "require_ticket", _require_ticket)
    monkeypatch.setattr(
        stage_result.runtime, "read_active_work_item", lambda _target: "iteration_id=I1"
    )
    monkeypatch.setattr(
        stage_result.runtime,
        "resolve_scope_key",
        lambda raw, ticket: scope_key if raw else f"{ticket}-scope",
    )
    monkeypatch.setattr(stage_result.runtime, "is_valid_work_item_key", lambda _value: True)
    monkeypatch.setattr(stage_result.runtime, "load_gates_config", lambda _target: {})
    monkeypatch.setattr(
        stage_result.runtime,
        "review_report_template",
        lambda _target: "aidd/reports/reviewer/{ticket}/{scope_key}.json",
    )


def test_main_review_blocks_when_context_pack_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "aidd"
    target.mkdir()
    _mock_runtime_context(monkeypatch, target, default_ticket="TK-9", scope_key="scope-review")
    monkeypatch.setattr(stage_result, "_tests_policy", lambda *_a, **_k: (False, False, ""))
    monkeypatch.setattr(
        stage_result, "_resolve_tests_evidence", lambda *_a, **_k: (None, False, None)
    )
    monkeypatch.setattr(stage_result, "_load_review_pack_verdict", lambda *_a, **_k: "")
    monkeypatch.setattr(stage_result, "_review_context_pack_placeholder", lambda *_a, **_k: False)

    exit_code = stage_result.main(
        [
            "--stage",
            "review",
            "--result",
            "done",
            "--ticket",
            "TK-9",
            "--work-item-key",
            "iteration_id=I1",
        ]
    )
    assert exit_code == 0

    payload_path = (
        target / "reports" / "loops" / "TK-9" / "scope-review" / "stage.review.result.json"
    )
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert payload["result"] == "blocked"
    assert payload["reason_code"] == "review_context_pack_missing"
    assert payload["verdict"] == "BLOCKED"


def test_main_qa_marks_tests_failed_as_blocked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "aidd"
    target.mkdir()
    _mock_runtime_context(monkeypatch, target, default_ticket="TK-10", scope_key="scope-qa")
    monkeypatch.setattr(stage_result, "_tests_policy", lambda *_a, **_k: (False, False, ""))
    monkeypatch.setattr(
        stage_result,
        "_resolve_tests_evidence",
        lambda *_a, **_k: ("aidd/reports/tests/TK-10.log", False, {"status": "fail"}),
    )
    monkeypatch.setattr(stage_result, "_load_qa_report_status", lambda *_a, **_k: "READY")

    exit_code = stage_result.main(
        [
            "--stage",
            "qa",
            "--result",
            "done",
            "--ticket",
            "TK-10",
        ]
    )
    assert exit_code == 0

    payload_path = target / "reports" / "loops" / "TK-10" / "TK-10-scope" / "stage.qa.result.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert payload["result"] == "blocked"
    assert payload["reason_code"] == "qa_tests_failed"
    assert payload["evidence_links"]["tests_log"] == "aidd/reports/tests/TK-10.log"


def test_main_implement_soft_tests_requirement_sets_continue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "aidd"
    target.mkdir()
    _mock_runtime_context(monkeypatch, target, default_ticket="TK-11", scope_key="scope-impl")
    monkeypatch.setattr(stage_result, "_tests_policy", lambda *_a, **_k: (True, False, ""))
    monkeypatch.setattr(
        stage_result, "_resolve_tests_evidence", lambda *_a, **_k: (None, False, None)
    )

    from aidd_runtime.reports import tests_log

    monkeypatch.setattr(tests_log, "append_log", lambda *_a, **_k: None)
    monkeypatch.setattr(
        tests_log,
        "tests_log_path",
        lambda target, ticket, scope_key: target
        / "reports"
        / "tests"
        / ticket
        / f"{scope_key}.jsonl",
    )

    exit_code = stage_result.main(
        [
            "--stage",
            "implement",
            "--result",
            "blocked",
            "--ticket",
            "TK-11",
            "--work-item-key",
            "iteration_id=I1",
        ]
    )
    assert exit_code == 0

    payload_path = (
        target / "reports" / "loops" / "TK-11" / "scope-impl" / "stage.implement.result.json"
    )
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert payload["requested_result"] == "blocked"
    assert payload["result"] == "continue"
    assert payload["reason_code"] == "no_tests_soft"
