from __future__ import annotations

from pathlib import Path

import pytest

from aidd_runtime import progress
from aidd_runtime.feature_ids import FeatureIdentifiers


def _config(**overrides: object) -> progress.ProgressConfig:
    data = {
        "enabled": True,
        "code_prefixes": ("src/",),
        "code_globs": (),
        "skip_branches": (),
        "allow_missing_tasklist": False,
        "override_env": None,
        "sources": (),
    }
    data.update(overrides)
    return progress.ProgressConfig(**data)


def test_progress_log_helpers_and_diff_utils() -> None:
    lines = [
        "- 2026-02-20 source=implement id=I1 kind=iteration hash=abc msg=done",
        "- 2026-02-20 source=implement id=I1 kind=iteration hash=abc msg=done",
        "- invalid",
    ]
    parsed, invalid = progress.parse_progress_log_lines(lines)
    assert len(parsed) == 2
    assert len(invalid) == 1

    deduped = progress.dedupe_progress_log(parsed)
    assert len(deduped) == 1

    normalized, archived, summary = progress.normalize_progress_log(lines, max_lines=1)
    assert len(normalized) == 1
    assert archived == []
    assert "invalid=1" in summary

    old_text = "- [ ] a\n- [x] done-old\n"
    new_text = "- [ ] a\n- [x] done-old\n- [x] done-new\n"
    assert progress._diff_checked(old_text, new_text) == ["- [x] done-new"]

    handoff_new = "- [ ] handoff no link\n- [ ] handoff linked aidd/reports/qa/TK.json\n"
    assert progress._diff_open_tasks("", handoff_new, require_reference=True) == [
        "- [ ] handoff linked aidd/reports/qa/TK.json"
    ]


def test_is_code_file_rules_and_format_helpers() -> None:
    cfg = _config(code_globs=("generated/*.tmp",))
    assert progress._is_code_file("src/main.py", cfg) is True
    assert progress._is_code_file("generated/build.tmp", cfg) is True
    assert progress._is_code_file("docs/readme.md", cfg) is False
    assert progress._is_code_file("aidd/docs/tasklist/TK-1.md", cfg) is False

    assert progress._summarise_paths(["a", "b", "c", "d"], limit=2) == "a, b, … (+2)"
    assert progress._format_list(["x", "y"], prefix="* ", limit=5) == "* x\n* y"


def test_check_progress_skip_and_error_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "repo"
    root.mkdir()

    monkeypatch.setattr(
        progress,
        "resolve_identifiers",
        lambda *_args, **_kwargs: FeatureIdentifiers(ticket="TK-1", slug_hint="tk-1"),
    )

    disabled = progress.check_progress(root, None, config=_config(enabled=False))
    assert disabled.status == "skip:disabled"

    skip_source = progress.check_progress(
        root, None, source="manual", config=_config(sources=("qa",))
    )
    assert skip_source.status == "skip:source"

    branch_skip = progress.check_progress(
        root,
        None,
        branch="feature/x",
        config=_config(skip_branches=("feature/*",)),
    )
    assert branch_skip.status == "skip:branch"

    monkeypatch.setattr(progress, "_collect_changed_files", lambda _root: (["src/app.py"], True))
    monkeypatch.setattr(
        progress,
        "resolve_identifiers",
        lambda *_args, **_kwargs: FeatureIdentifiers(ticket=None, slug_hint=None),
    )
    missing_ticket = progress.check_progress(root, None, config=_config())
    assert missing_ticket.status == "error:no-ticket"

    monkeypatch.setattr(
        progress,
        "resolve_identifiers",
        lambda *_args, **_kwargs: FeatureIdentifiers(ticket="TK-1", slug_hint="tk-1"),
    )
    missing_tasklist = progress.check_progress(root, None, config=_config())
    assert missing_tasklist.status == "error:no-tasklist"

    skipped_missing = progress.check_progress(
        root, None, config=_config(allow_missing_tasklist=True)
    )
    assert skipped_missing.status == "skip:missing-tasklist"


def test_check_progress_success_and_block_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "repo"
    tasklist = root / "docs" / "tasklist" / "TK-2.md"
    tasklist.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        progress,
        "resolve_identifiers",
        lambda *_args, **_kwargs: FeatureIdentifiers(ticket="TK-2", slug_hint="tk-2"),
    )
    monkeypatch.setattr(progress, "_collect_changed_files", lambda _root: (["src/app.py"], True))

    tasklist.write_text("- [x] implemented\n", encoding="utf-8")
    monkeypatch.setattr(progress, "_read_git_file", lambda _root, _rel: "- [ ] todo\n")
    ok_result = progress.check_progress(root, None, source="implement", config=_config())
    assert ok_result.status == "ok"
    assert ok_result.new_items == ["- [x] implemented"]
    assert "Tasklist progress confirmed." in progress._build_success_message(ok_result)

    tasklist.write_text("- [ ] handoff aidd/reports/qa/TK-2.json\n", encoding="utf-8")
    monkeypatch.setattr(progress, "_read_git_file", lambda _root, _rel: "")
    handoff_ok = progress.check_progress(root, None, source="handoff", config=_config())
    assert handoff_ok.status == "ok"

    tasklist.write_text("- [ ] unchanged\n", encoding="utf-8")
    monkeypatch.setattr(progress, "_read_git_file", lambda _root, _rel: "- [ ] unchanged\n")
    blocked = progress.check_progress(root, None, source="implement", config=_config())
    assert blocked.status == "error:no-checkbox"
    assert "BLOCK:" in blocked.message
