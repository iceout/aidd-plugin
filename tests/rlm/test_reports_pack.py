from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd_runtime import reports_pack


def test_budget_compact_and_filter_helpers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    errors = reports_pack.check_budget("x\n" * 5, max_chars=2, max_lines=2, label="qa")
    assert len(errors) == 2
    assert reports_pack._check_count_budget("qa", field="findings", actual=3, limit=2)
    assert reports_pack._check_count_budget("qa", field="findings", actual=2, limit=2) == []

    assert reports_pack._is_empty(None) is True
    assert reports_pack._is_empty("  ") is True
    assert reports_pack._is_empty([]) is True
    assert reports_pack._is_empty({}) is True
    assert reports_pack._is_empty("x") is False

    compacted = reports_pack._compact_value(
        {
            "a": "",
            "b": {"cols": ["c"], "rows": []},
            "c": [None, "", {"k": "v"}],
        }
    )
    assert compacted["b"] == {"cols": ["c"], "rows": []}
    assert compacted["c"] == [{"k": "v"}]

    payload = {
        "schema": "aidd.report.pack.v1",
        "pack_version": "v1",
        "type": "qa",
        "kind": "report",
        "ticket": "TK-1",
        "slug": None,
        "slug_hint": None,
        "generated_at": "now",
        "source_path": "qa.json",
        "empty": [],
        "keep": {"k": "v"},
    }
    compact_payload = reports_pack._compact_payload(payload)
    assert "empty" not in compact_payload
    assert "keep" in compact_payload

    monkeypatch.setenv("AIDD_PACK_ALLOW_FIELDS", "schema,stats")
    monkeypatch.setenv("AIDD_PACK_STRIP_FIELDS", "stats")
    serialized = reports_pack._serialize_pack({**payload, "stats": {"a": 1}, "extra": "x"})
    parsed = json.loads(serialized)
    assert "schema" in parsed
    assert "extra" not in parsed
    assert "stats" not in parsed

    out = tmp_path / "pack.json"
    reports_pack._write_pack_text(serialized, out)
    assert out.exists()

    monkeypatch.setenv("AIDD_PACK_ENFORCE_BUDGET", "1")
    assert reports_pack._enforce_budget() is True


def test_trim_helpers_and_auto_trim_paths() -> None:
    payload = {
        "schema": "aidd.report.pack.v1",
        "pack_version": "v1",
        "type": "research",
        "kind": "context",
        "ticket": "TK-1",
        "slug": "tk-1",
        "slug_hint": "tk-1",
        "generated_at": "now",
        "source_path": "x.json",
        "matches": {"cols": ["a"], "rows": [[1], [2]]},
        "reuse_candidates": {"cols": ["a"], "rows": [[1]]},
        "manual_notes": ["n1", "n2"],
        "profile": {
            "recommendations": ["r1"],
            "tests_evidence": ["e1", "e2"],
            "suggested_test_tasks": ["t1"],
            "logging_artifacts": ["l1"],
        },
        "paths": [{"path": "src", "sample": [1, 2]}],
        "docs": [{"path": "docs", "sample": [1]}],
        "paths_discovered": ["src", "tests"],
        "invalid_paths": ["x", "y"],
        "keywords_raw": ["A", "B"],
        "keywords": ["a", "b"],
        "stats": {"matches": 2},
    }
    assert reports_pack._trim_columnar_rows(payload, "matches") is True
    assert reports_pack._trim_list_field(payload, "manual_notes") is True
    assert reports_pack._trim_profile_recommendations(payload) is True
    assert reports_pack._trim_profile_list(payload, "tests_evidence") is True
    assert reports_pack._trim_path_samples(payload, "paths") is True
    payload["empty_col"] = {"cols": [], "rows": []}
    assert reports_pack._drop_columnar_if_empty(payload, "empty_col") is True
    assert reports_pack._drop_field(payload, "stats") is True

    big_research = {
        "schema": "aidd.report.pack.v1",
        "pack_version": "v1",
        "type": "research",
        "kind": "context",
        "ticket": "TK-1",
        "slug": "tk-1",
        "slug_hint": "tk-1",
        "generated_at": "now",
        "source_path": "x.json",
        "manual_notes": [f"note-{i}" for i in range(20)],
        "matches": {"cols": ["id"], "rows": [[i] for i in range(20)]},
        "reuse_candidates": {"cols": ["id"], "rows": [[i] for i in range(10)]},
        "paths": [{"path": "src", "sample": [str(i) for i in range(10)]}],
        "docs": [{"path": "docs", "sample": [str(i) for i in range(10)]}],
        "profile": {"recommendations": [f"r{i}" for i in range(10)]},
    }
    text, trimmed, errors = reports_pack._auto_trim_research_pack(
        big_research, max_chars=400, max_lines=40
    )
    assert isinstance(text, str)
    assert trimmed
    assert errors == []

    rlm_pack = {
        "schema": "aidd.report.pack.v1",
        "pack_version": "v1",
        "type": "rlm",
        "kind": "pack",
        "ticket": "TK-1",
        "slug": "tk-1",
        "slug_hint": "tk-1",
        "generated_at": "now",
        "source_path": "x.json",
        "warnings": ["w1"],
        "stats": {"nodes": 1},
        "entrypoints": [{"file_id": "a"} for _ in range(6)],
        "hotspots": [{"file_id": "a"} for _ in range(6)],
        "integration_points": [{"file_id": "a"} for _ in range(6)],
        "test_hooks": [{"file_id": "a"} for _ in range(6)],
        "risks": [{"file_id": "a"} for _ in range(6)],
        "recommended_reads": [{"file_id": "a"} for _ in range(6)],
        "links": [{"evidence_snippet": "x" * 200} for _ in range(10)],
    }
    assert reports_pack._max_snippet_len(rlm_pack) == 200
    assert reports_pack._trim_evidence_snippets(rlm_pack, 50) is True
    text2, trimmed2, errors2, trim_stats = reports_pack._auto_trim_rlm_pack(
        rlm_pack, max_chars=900, max_lines=80
    )
    assert isinstance(text2, str)
    assert trimmed2
    assert errors2 == []
    assert isinstance(trim_stats, dict)


def test_env_limits_and_jsonl_helpers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    reports_pack._ENV_LIMITS_CACHE = None
    monkeypatch.setenv("AIDD_PACK_LIMITS", '{"qa":{"findings":"3"},"bad":"x"}')
    assert reports_pack._env_limits()["qa"]["findings"] == 3
    # Cache hit should still return parsed data
    assert reports_pack._env_limits()["qa"]["findings"] == 3
    reports_pack._ENV_LIMITS_CACHE = None

    path = tmp_path / "rows.jsonl"
    path.write_text('{"a":1}\ninvalid\n{"b":2}\n', encoding="utf-8")
    assert reports_pack._load_jsonl(path) == [{"a": 1}, {"b": 2}]
    assert reports_pack._load_jsonl(tmp_path / "missing.jsonl") == []

    assert reports_pack._pack_path_for(Path("qa.json")).name.endswith(".pack.json")
    assert reports_pack._pack_path_for(Path("already.pack.json")).name == "already.pack.json"


def test_write_pack_wrappers_and_main(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "aidd"
    root.mkdir()

    research_json = root / "reports" / "research" / "TK-1.json"
    qa_json = root / "reports" / "qa" / "TK-1.json"
    prd_json = root / "reports" / "prd" / "TK-1.json"
    for path in (research_json, qa_json, prd_json):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"ticket": "TK-1"}), encoding="utf-8")

    monkeypatch.setenv("AIDD_PACK_ALLOW_FIELDS", "")
    monkeypatch.setenv("AIDD_PACK_STRIP_FIELDS", "")
    reports_pack._ENV_LIMITS_CACHE = None

    monkeypatch.setattr(
        reports_pack,
        "build_research_pack",
        lambda payload, **_k: {
            "schema": "aidd.report.pack.v1",
            "pack_version": "v1",
            "type": "research",
            "kind": "context",
            "ticket": payload.get("ticket"),
            "slug": "tk-1",
            "slug_hint": "tk-1",
            "generated_at": "now",
            "source_path": "x",
        },
    )
    monkeypatch.setattr(
        reports_pack, "_auto_trim_research_pack", lambda pack, **_k: (json.dumps(pack), [], [])
    )
    monkeypatch.setattr(
        reports_pack,
        "build_qa_pack",
        lambda payload, **_k: {
            "schema": "aidd.report.pack.v1",
            "pack_version": "v1",
            "type": "qa",
            "kind": "report",
            "ticket": payload.get("ticket"),
            "slug": None,
            "slug_hint": None,
            "generated_at": "now",
            "source_path": "x",
        },
    )
    monkeypatch.setattr(
        reports_pack,
        "build_prd_pack",
        lambda payload, **_k: {
            "schema": "aidd.report.pack.v1",
            "pack_version": "v1",
            "type": "prd",
            "kind": "review",
            "ticket": payload.get("ticket"),
            "slug": "tk-1",
            "slug_hint": None,
            "generated_at": "now",
            "source_path": "x",
        },
    )

    rp = reports_pack.write_research_pack(research_json, root=root)
    qp = reports_pack.write_qa_pack(qa_json, root=root)
    pp = reports_pack.write_prd_pack(prd_json, root=root)
    assert rp.exists() and rp.name.endswith(".pack.json")
    assert qp.exists() and qp.name.endswith(".pack.json")
    assert pp.exists() and pp.name.endswith(".pack.json")

    nodes_path = root / "reports" / "research" / "TK-2-rlm.nodes.jsonl"
    links_path = root / "reports" / "research" / "TK-2-rlm.links.jsonl"
    nodes_path.write_text(
        '{"node_kind":"file","file_id":"a","path":"src/a.py"}\n', encoding="utf-8"
    )
    links_path.write_text('{"link_id":"l1"}\n', encoding="utf-8")
    monkeypatch.setattr(reports_pack, "load_rlm_settings", lambda _root: {})
    monkeypatch.setattr(
        reports_pack,
        "build_rlm_pack",
        lambda nodes, links, **_k: {
            "schema": "aidd.report.pack.v1",
            "pack_version": "v1",
            "type": "rlm",
            "kind": "pack",
            "ticket": "TK-2",
            "slug": "tk-2",
            "slug_hint": None,
            "generated_at": "now",
            "source_path": "x",
            "links": [],
        },
    )
    monkeypatch.setattr(
        reports_pack, "_auto_trim_rlm_pack", lambda pack, **_k: (json.dumps(pack), [], [], {})
    )
    monkeypatch.setattr(reports_pack.runtime, "rel_path", lambda path, _root: path.name)

    rlm_pack_path = reports_pack.write_rlm_pack(nodes_path, links_path, root=root)
    assert rlm_pack_path.exists()

    with pytest.raises(SystemExit, match="must be provided together"):
        reports_pack.main(["--rlm-nodes", str(nodes_path)])

    rc = reports_pack.main(["--rlm-nodes", str(nodes_path), "--rlm-links", str(links_path)])
    assert rc == 0
