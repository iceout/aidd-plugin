from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd_runtime import rlm_verify


def test_symbol_variants_and_validate_symbols() -> None:
    assert rlm_verify._symbol_variants("pkg.mod.func") == ["pkg.mod.func", "func"]
    assert rlm_verify._symbol_variants("ns::Type") == ["ns::Type", "Type"]
    assert rlm_verify._symbol_variants("") == []

    text = "call func and Type and direct_symbol"
    missing = rlm_verify._validate_symbols(text, ["pkg.mod.func", "ns::Type", "missing"])
    assert missing == ["missing"]


def test_verify_nodes_updates_statuses(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    project = workspace / "aidd"
    project.mkdir(parents=True)
    src = workspace / "src"
    src.mkdir()
    (src / "ok.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    (src / "partial.py").write_text("foo\n", encoding="utf-8")

    nodes_path = project / "reports" / "research" / "TK-1-rlm.nodes.jsonl"
    nodes_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {"node_kind": "file", "file_id": "a", "path": "src/ok.py", "public_symbols": ["foo"]},
        {
            "node_kind": "file",
            "file_id": "b",
            "path": "src/partial.py",
            "public_symbols": ["foo", "bar"],
        },
        {"node_kind": "file", "file_id": "c", "path": "src/missing.py", "public_symbols": ["x"]},
        {"node_kind": "file", "file_id": "d", "public_symbols": ["x"]},
    ]
    nodes_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    updated = rlm_verify.verify_nodes(project, workspace, nodes_path, max_file_bytes=1024)
    assert updated == 4

    updated_rows = rlm_verify._iter_nodes(nodes_path)
    status_by_id = {str(item["file_id"]): item["verification"] for item in updated_rows}
    assert status_by_id["a"] == "passed"
    assert status_by_id["b"] == "partial"
    assert status_by_id["c"] == "failed"
    assert status_by_id["d"] == "failed"


def test_main_uses_runtime_context(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    project = workspace / "aidd"
    nodes_path = project / "reports" / "research" / "TK-2-rlm.nodes.jsonl"
    nodes_path.parent.mkdir(parents=True, exist_ok=True)
    nodes_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(rlm_verify.runtime, "require_workflow_root", lambda: (workspace, project))
    monkeypatch.setattr(
        rlm_verify.runtime,
        "require_ticket",
        lambda _target, ticket=None, slug_hint=None: ("TK-2", object()),
    )
    monkeypatch.setattr(rlm_verify, "load_rlm_settings", lambda _target: {"max_file_bytes": 5})
    calls: list[tuple[Path, Path, Path, int]] = []

    def fake_verify(
        project_root: Path, workspace_root: Path, path: Path, *, max_file_bytes: int
    ) -> int:
        calls.append((project_root, workspace_root, path, max_file_bytes))
        return 3

    monkeypatch.setattr(rlm_verify, "verify_nodes", fake_verify)
    monkeypatch.setattr(rlm_verify.runtime, "rel_path", lambda path, _root: path.name)

    rc = rlm_verify.main(["--ticket", "TK-2"])
    assert rc == 0
    assert calls == [(project, workspace, nodes_path, 5)]


def test_main_raises_when_nodes_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    project = workspace / "aidd"
    project.mkdir(parents=True)
    monkeypatch.setattr(rlm_verify.runtime, "require_workflow_root", lambda: (workspace, project))
    monkeypatch.setattr(
        rlm_verify.runtime,
        "require_ticket",
        lambda _target, ticket=None, slug_hint=None: ("TK-X", object()),
    )
    monkeypatch.setattr(rlm_verify, "load_rlm_settings", lambda _target: {})

    with pytest.raises(SystemExit, match="rlm nodes not found"):
        rlm_verify.main(["--ticket", "TK-X"])
