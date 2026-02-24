from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from aidd_runtime import rlm_nodes_build
from aidd_runtime.rlm_config import file_id_for_path


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_split_normalize_and_match_helpers(tmp_path: Path) -> None:
    base_root = tmp_path / "workspace"
    base_root.mkdir()
    (base_root / "src").mkdir()
    assert rlm_nodes_build._split_values(["src, tests", None, "src"]) == ["src", "tests"]
    normalized = rlm_nodes_build._normalize_worklist_paths(
        [str(base_root / "src"), "pkg/api"], base_root=base_root
    )
    assert normalized[0].endswith("/workspace/src")
    assert normalized[1] == "pkg/api"
    assert rlm_nodes_build._normalize_worklist_keywords(["foo, bar", "foo"]) == ["foo", "bar"]
    assert rlm_nodes_build._matches_prefix("src/app.py", ["src"]) is True
    assert rlm_nodes_build._matches_prefix("docs/readme.md", ["src"]) is False


def test_filter_manifest_entries_by_paths_and_keywords(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "aidd"
    base_root = tmp_path / "workspace"
    base_root.mkdir()
    manifest = {
        "files": [
            {"path": "src/a.py", "file_id": "a"},
            {"path": "src/b.py", "file_id": "b"},
            {"path": "docs/c.md", "file_id": "c"},
        ]
    }
    monkeypatch.setattr(rlm_nodes_build, "_resolve_base_root", lambda *_a, **_k: base_root)
    monkeypatch.setattr(
        rlm_nodes_build, "_resolve_keyword_roots", lambda *_a, **_k: [base_root / "src"]
    )
    monkeypatch.setattr(
        rlm_nodes_build.rlm_targets,
        "rg_files_with_matches",
        lambda *_a, **_k: {"src/b.py"},
    )

    entries, scope = rlm_nodes_build._filter_manifest_entries(
        target,
        manifest,
        settings={"ignore_dirs": []},
        worklist_paths=["src"],
        worklist_keywords=["needle"],
    )
    assert [item["path"] for item in entries] == ["src/b.py"]
    assert scope is not None
    assert scope["counts"]["manifest_total"] == 3
    assert scope["counts"]["entries_selected"] == 1


def test_compact_nodes_and_build_dir_nodes() -> None:
    file_a = {
        "node_kind": "file",
        "id": "id-a",
        "file_id": "id-a",
        "path": "src/api.py",
        "summary": "API handlers",
        "public_symbols": ["handle_a", "handle_b"],
        "framework_roles": ["web"],
        "test_hooks": ["pytest -k api"],
        "risks": [],
    }
    file_b = {
        "node_kind": "file",
        "id": "id-b",
        "file_id": "id-b",
        "path": "src/service.py",
        "summary": "Service layer",
        "public_symbols": ["Service"],
        "framework_roles": ["service"],
        "test_hooks": [],
        "risks": ["io"],
    }
    duplicate = {**file_a, "summary": "newer"}
    compacted = rlm_nodes_build._compact_nodes([file_a, duplicate, file_b])
    assert [item["id"] for item in compacted] == ["id-a", "id-b"]
    assert compacted[0]["summary"] == "newer"

    dir_nodes = rlm_nodes_build.build_dir_nodes(compacted, max_children=10, max_chars=400)
    src_node = next(item for item in dir_nodes if item["path"] == "src")
    assert "Entrypoints:" in str(src_node["summary"])
    assert src_node["children_count_total"] == 2


def test_build_worklist_and_pack(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    nodes_path = tmp_path / "nodes.jsonl"
    manifest_entries = [
        {"file_id": "a", "path": "src/a.py", "rev_sha": "1", "prompt_version": "v1", "lang": "py"},
        {"file_id": "b", "path": "src/b.py", "rev_sha": "2", "prompt_version": "v1", "lang": "py"},
        {"file_id": "c", "path": "src/c.py", "rev_sha": "3", "prompt_version": "v1", "lang": "py"},
    ]
    _write_jsonl(
        nodes_path,
        [
            {
                "node_kind": "file",
                "file_id": "a",
                "rev_sha": "1",
                "prompt_version": "v1",
                "verification": "passed",
            },
            {
                "node_kind": "file",
                "file_id": "b",
                "rev_sha": "x",
                "prompt_version": "v1",
                "verification": "passed",
            },
            {
                "node_kind": "file",
                "file_id": "c",
                "rev_sha": "3",
                "prompt_version": "v1",
                "verification": "failed",
            },
        ],
    )
    worklist, stats = rlm_nodes_build._build_worklist(manifest_entries, nodes_path)
    assert [item["reason"] for item in worklist] == ["outdated", "failed"]
    assert stats == {"missing": 0, "outdated": 1, "failed": 1}

    target = tmp_path / "aidd"
    target.mkdir()
    manifest_path = target / "reports" / "research" / "TK-1-rlm-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({"slug_hint": "tk-1", "files": manifest_entries}), encoding="utf-8"
    )
    monkeypatch.setattr(
        rlm_nodes_build, "load_rlm_settings", lambda _t: {"worklist_max_entries": 1}
    )
    monkeypatch.setattr(
        rlm_nodes_build,
        "_filter_manifest_entries",
        lambda *_a, **_k: (manifest_entries, {"paths": ["src"], "keywords": [], "counts": {}}),
    )
    monkeypatch.setattr(rlm_nodes_build.runtime, "rel_path", lambda path, _root: path.name)
    pack = rlm_nodes_build.build_worklist_pack(
        target,
        "TK-1",
        manifest_path=manifest_path,
        nodes_path=nodes_path,
    )
    assert pack["status"] == "pending"
    assert pack["stats"]["entries_total"] == 2
    assert pack["stats"]["entries_trimmed"] == 1
    assert len(pack["entries"]) == 1
    assert pack["worklist_scope"]["paths"] == ["src"]


def test_main_bootstrap_and_refresh_worklist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "aidd"
    target.mkdir()
    manifest_path = target / "reports" / "research" / "TK-3-rlm-manifest.json"
    nodes_path = target / "reports" / "research" / "TK-3-rlm.nodes.jsonl"
    output = target / "reports" / "research" / "TK-3-rlm.worklist.pack.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({"files": [{"file_id": "x", "path": "src/x.py"}]}), encoding="utf-8"
    )
    output.write_text(
        json.dumps({"worklist_scope": {"paths": ["src"], "keywords": ["needle"]}}), encoding="utf-8"
    )

    monkeypatch.setattr(
        rlm_nodes_build.runtime, "require_workflow_root", lambda: (tmp_path, target)
    )
    monkeypatch.setattr(
        rlm_nodes_build.runtime,
        "require_ticket",
        lambda _target, ticket=None, slug_hint=None: ("TK-3", SimpleNamespace()),
    )
    monkeypatch.setattr(rlm_nodes_build.runtime, "rel_path", lambda path, _root: path.name)
    monkeypatch.setattr(
        rlm_nodes_build.runtime, "resolve_path_for_target", lambda path, _root: target / path
    )

    # bootstrap branch
    monkeypatch.setattr(
        rlm_nodes_build,
        "_load_manifest",
        lambda _path: {"files": [{"file_id": "x", "path": "src/x.py"}]},
    )
    monkeypatch.setattr(
        rlm_nodes_build,
        "_build_bootstrap_nodes",
        lambda _manifest: [{"id": "x", "file_id": "x", "node_kind": "file", "path": "src/x.py"}],
    )
    monkeypatch.setattr(rlm_nodes_build, "_compact_nodes", lambda nodes: list(nodes))
    rc_bootstrap = rlm_nodes_build.main(["--ticket", "TK-3", "--bootstrap"])
    assert rc_bootstrap == 0
    assert nodes_path.exists()

    # refresh worklist branch (preserve scope from existing output)
    monkeypatch.setattr(
        rlm_nodes_build,
        "build_worklist_pack",
        lambda *_a, **kwargs: {
            "schema": "aidd.report.pack.v1",
            "type": "rlm-worklist",
            "ticket": "TK-3",
            "status": "ready",
            "entries": [],
            "args_scope": {
                "worklist_paths": kwargs.get("worklist_paths"),
                "worklist_keywords": kwargs.get("worklist_keywords"),
            },
        },
    )
    rc_refresh = rlm_nodes_build.main(["--ticket", "TK-3", "--refresh-worklist"])
    assert rc_refresh == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["args_scope"]["worklist_paths"] == ["src"]
    assert payload["args_scope"]["worklist_keywords"] == ["needle"]
