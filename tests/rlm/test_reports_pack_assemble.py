from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd_runtime import reports_pack_assemble as assemble


def test_basic_helpers_and_evidence_snippet(tmp_path: Path) -> None:
    assert assemble.truncate_list([1, 2, 3], 2) == [1, 2]
    assert assemble.truncate_list([1, 2, 3], 0) == []
    assert assemble.truncate_text("abcdef", 4) == "abcd"
    assert assemble.truncate_text("abc", 0) == ""

    root = tmp_path / "aidd"
    root.mkdir()
    src = root.parent / "src.py"
    src.write_text("l1\nl2 token\nl3\n", encoding="utf-8")
    snippet = assemble.extract_evidence_snippet(
        root,
        {"path": "src.py", "line_start": 2, "line_end": 2},
        max_chars=20,
    )
    assert snippet == "l2 token"
    assert assemble.extract_evidence_snippet(root, {"path": "missing.py"}, max_chars=10) == ""

    sid = assemble.stable_id("a", 1)
    assert sid == assemble.stable_id("a", 1)
    assert sid != assemble.stable_id("a", 2)
    assert assemble.columnar(["a"], [[1]]) == {"cols": ["a"], "rows": [[1]]}


def test_pack_helpers_and_rlm_links_stats(tmp_path: Path) -> None:
    paths = assemble.pack_paths([{"path": "src/a.py", "sample": [1, 2, 3], "exists": True}], 5, 2)
    assert paths[0]["sample"] == [1, 2]

    matches = assemble.pack_matches(
        [{"token": "foo", "file": "src/a.py", "line": 3, "snippet": "x" * 100}],
        limit=3,
        snippet_limit=10,
    )
    assert matches["cols"] == ["id", "token", "file", "line", "snippet"]
    assert matches["rows"][0][1] == "foo"
    assert len(matches["rows"][0][-1]) <= 10

    reuse = assemble.pack_reuse(
        [{"path": "src/a.py", "language": "py", "score": 9, "top_symbols": [1, 2, 3, 4]}],
        limit=2,
    )
    assert reuse["rows"][0][1] == "src/a.py"
    assert len(reuse["rows"][0][5]) == 3

    tests = assemble.pack_tests_executed(
        [{"command": "pytest", "status": "pass", "log_path": "a.log", "exit_code": 0}], 2
    )
    assert tests["rows"][0] == ["pytest", "pass", "a.log", 0]

    rlm_stats_path = tmp_path / "reports" / "research" / "TK-1-rlm.links.stats.json"
    rlm_stats_path.parent.mkdir(parents=True, exist_ok=True)
    rlm_stats_path.write_text(
        json.dumps(
            {
                "links_total": 0,
                "links_truncated": True,
                "target_files_trimmed": 1,
                "symbols_truncated": 1,
                "candidate_truncated": 1,
                "rg_timeouts": 1,
                "rg_errors": 1,
                "target_files_total": 0,
            }
        ),
        encoding="utf-8",
    )
    stats = assemble.load_rlm_links_stats(tmp_path, "TK-1")
    assert stats is not None
    warnings = assemble.rlm_link_warnings(stats)
    assert "rlm_links_empty_warn" in warnings
    assert "rlm rg timeout during link search" in warnings


def test_worklist_summary_and_builders(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "aidd"
    root.mkdir()
    worklist_path = root / "reports" / "research" / "TK-2-rlm.worklist.pack.json"
    worklist_path.parent.mkdir(parents=True, exist_ok=True)
    worklist_path.write_text(
        json.dumps({"status": "pending", "entries": [{"a": 1}, {"b": 2}]}), encoding="utf-8"
    )
    monkeypatch.setattr(
        assemble.runtime, "resolve_path_for_target", lambda path, _root: root / path
    )

    status, count, resolved = assemble.load_rlm_worklist_summary(
        root, "TK-2", context={"rlm_worklist_path": "reports/research/TK-2-rlm.worklist.pack.json"}
    )
    assert (status, count) == ("pending", 2)
    assert resolved == worklist_path

    monkeypatch.setattr(assemble.core, "_env_limits", lambda: {})
    monkeypatch.setattr(assemble.core, "_utc_timestamp", lambda: "2026-02-24T00:00:00Z")
    monkeypatch.setattr(assemble, "load_rlm_links_stats", lambda *_a, **_k: {"links_total": 2})
    monkeypatch.setattr(assemble, "rlm_link_warnings", lambda _stats: ["rlm-warning"])
    monkeypatch.setattr(
        assemble, "load_rlm_worklist_summary", lambda *_a, **_k: ("pending", 3, None)
    )
    monkeypatch.setattr(
        assemble, "load_rlm_settings", lambda _root: {"link_unverified_warn_ratio": 0.4}
    )

    targets_json = root / "reports" / "research" / "TK-2-rlm-targets.json"
    targets_json.write_text(json.dumps({"keyword_hits": ["src/entry.py"]}), encoding="utf-8")

    nodes = [
        {
            "node_kind": "file",
            "file_id": "f-entry",
            "path": "src/entry.py",
            "summary": "entry",
            "framework_roles": ["web"],
            "test_hooks": ["pytest"],
            "risks": [],
        },
        {
            "node_kind": "file",
            "file_id": "f-svc",
            "path": "src/service.py",
            "summary": "svc",
            "framework_roles": ["service"],
            "test_hooks": [],
            "risks": ["io"],
        },
    ]
    links = [
        {"link_id": "l1", "src_file_id": "f-entry", "dst_file_id": "f-svc", "type": "calls"},
        {
            "link_id": "l2",
            "src_file_id": "f-svc",
            "dst_file_id": "f-entry",
            "type": "uses",
            "unverified": True,
        },
    ]
    pack = assemble.build_rlm_pack(
        nodes,
        links,
        ticket="TK-2",
        slug_hint="tk-2",
        source_path="aidd/reports/research/TK-2-rlm.nodes.jsonl",
        root=root,
    )
    assert pack["type"] == "rlm"
    assert pack["status"] == "pending"
    assert pack["stats"]["links_unverified"] == 1
    assert pack["stats"]["worklist_entries"] == 3
    assert any(item["file_id"] == "f-entry" for item in pack["entrypoints"])
    assert "warnings" in pack


def test_build_research_qa_prd_pack_shapes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(assemble.core, "_env_limits", lambda: {})

    research = assemble.build_research_pack(
        {
            "ticket": "TK-1",
            "slug_hint": "tk-1",
            "generated_at": "now",
            "paths": [{"path": "src", "sample": [1, 2]}],
            "docs": [],
            "profile": {"recommendations": ["a"], "tests_evidence": [], "suggested_test_tasks": []},
            "matches": [{"token": "x", "file": "src/a.py", "line": 1, "snippet": "hi"}],
            "reuse_candidates": [{"path": "src/a.py"}],
        },
        source_path="x.json",
    )
    assert research["type"] == "research"
    assert research["source_path"] == "x.json"

    qa = assemble.build_qa_pack(
        {
            "ticket": "TK-1",
            "generated_at": "now",
            "status": "READY",
            "findings": [{"id": "F1", "severity": "low"}],
            "tests_executed": [{"command": "pytest", "status": "pass", "exit_code": 0}],
        }
    )
    assert qa["type"] == "qa"
    assert qa["stats"]["findings"] == 1

    prd = assemble.build_prd_pack(
        {
            "ticket": "TK-1",
            "slug": "tk-1",
            "generated_at": "now",
            "status": "ok",
            "findings": [{"id": "P1"}],
            "action_items": ["a", "b"],
        }
    )
    assert prd["type"] == "prd"
    assert prd["stats"]["action_items"] == 2
