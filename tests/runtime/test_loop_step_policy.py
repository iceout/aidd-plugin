from __future__ import annotations

from pathlib import Path

from aidd_runtime import loop_step_policy
from aidd_runtime import loop_step_wrappers


def test_resolve_stream_mode_aliases() -> None:
    assert loop_step_policy.resolve_stream_mode("text+tools") == "tools"
    assert loop_step_policy.resolve_stream_mode("text-only") == "text"
    assert loop_step_policy.resolve_stream_mode("unknown") == "text"


def test_select_qa_repair_work_item_from_handoff_candidates() -> None:
    lines = [
        "## AIDD:HANDOFF_INBOX",
        "<!-- handoff:qa start -->",
        "- [ ] H1 - scope: iteration_id=I7 id: H1 (Blocking: true)",
        "<!-- handoff:qa end -->",
    ]
    work_item_key, reason_code, reason, labels = loop_step_policy._select_qa_repair_work_item(
        tasklist_lines=lines,
        explicit="",
        select_handoff=True,
        mode="auto",
    )
    assert work_item_key == "iteration_id=I7"
    assert reason_code == ""
    assert reason == ""
    assert labels == ["H1"]


def test_evaluate_wrapper_skip_policy_blocks_in_strict_mode(
    monkeypatch,
) -> None:
    plugin_root = Path(__file__).resolve().parents[2]
    monkeypatch.setenv("AIDD_SKIP_STAGE_WRAPPERS", "1")
    monkeypatch.setenv("AIDD_HOOKS_MODE", "strict")
    status, message, reason_code = loop_step_policy.evaluate_wrapper_skip_policy(
        "implement",
        plugin_root,
    )
    assert status == "blocked"
    assert "AIDD_SKIP_STAGE_WRAPPERS=1" in message
    assert reason_code == "wrappers_skipped_unsafe"


def test_resolve_runner_prefers_codex_profile(monkeypatch) -> None:
    plugin_root = Path(__file__).resolve().parents[2]
    monkeypatch.delenv("AIDD_LOOP_RUNNER", raising=False)
    monkeypatch.delenv("AIDD_RUNNER", raising=False)
    monkeypatch.setenv("AIDD_IDE_PROFILE", "codex")

    tokens, raw, notice = loop_step_wrappers.resolve_runner(None, plugin_root)
    assert raw == "codex"
    assert tokens[0] == "codex"
    assert "runner not configured" not in notice
