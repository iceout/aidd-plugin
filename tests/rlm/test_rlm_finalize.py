from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from aidd_runtime import rlm_finalize


def test_main_auto_bootstraps_missing_nodes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workspace = tmp_path / "ws"
    project = workspace / "aidd"
    nodes_path = project / "reports" / "research" / "TK-1-rlm.nodes.jsonl"
    links_path = project / "reports" / "research" / "TK-1-rlm.links.jsonl"
    project.mkdir(parents=True)
    links_path.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(rlm_finalize.runtime, "require_workflow_root", lambda: (workspace, project))
    monkeypatch.setattr(
        rlm_finalize.runtime,
        "require_ticket",
        lambda _target, ticket=None, slug_hint=None: ("TK-1", SimpleNamespace()),
    )
    monkeypatch.setattr(rlm_finalize.runtime, "resolve_path_for_target", lambda path, _root: path)

    calls: list[tuple[str, list[str]]] = []

    def fake_nodes_main(argv: list[str] | None = None) -> int:
        args = list(argv or [])
        calls.append(("nodes", args))
        if "--bootstrap" in args:
            nodes_path.write_text(
                json.dumps({"node_kind": "file", "file_id": "x", "path": "src/x.py"}) + "\n",
                encoding="utf-8",
            )
        return 0

    monkeypatch.setattr(rlm_finalize.rlm_nodes_build, "main", fake_nodes_main)
    monkeypatch.setattr(
        rlm_finalize.rlm_verify,
        "main",
        lambda argv=None: calls.append(("verify", list(argv or []))) or 0,
    )

    def fake_links_main(argv: list[str] | None = None) -> int:
        links_path.write_text('{"link_id":"l1"}\n', encoding="utf-8")
        calls.append(("links", list(argv or [])))
        return 0

    monkeypatch.setattr(rlm_finalize.rlm_links_build, "main", fake_links_main)
    monkeypatch.setattr(
        rlm_finalize.rlm_jsonl_compact,
        "main",
        lambda argv=None: calls.append(("compact", list(argv or []))) or 0,
    )
    monkeypatch.setattr(
        rlm_finalize.reports_pack,
        "main",
        lambda argv=None: calls.append(("pack", list(argv or []))) or 0,
    )

    rc = rlm_finalize.main(["--ticket", "TK-1"])
    assert rc == 0
    assert nodes_path.exists()

    assert calls[0][0] == "nodes"
    assert "--bootstrap" in calls[0][1]
    assert calls[1][0] == "verify"
    assert calls[2][0] == "links"
    assert calls[3][0] == "compact"
    assert calls[4][0] == "nodes"
    assert "--refresh-worklist" in calls[4][1]
    assert calls[5][0] == "pack"


def test_main_raises_when_missing_nodes_and_bootstrap_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workspace = tmp_path / "ws"
    project = workspace / "aidd"
    project.mkdir(parents=True)

    monkeypatch.setattr(rlm_finalize.runtime, "require_workflow_root", lambda: (workspace, project))
    monkeypatch.setattr(
        rlm_finalize.runtime,
        "require_ticket",
        lambda _target, ticket=None, slug_hint=None: ("TK-X", SimpleNamespace()),
    )
    monkeypatch.setattr(rlm_finalize.runtime, "resolve_path_for_target", lambda path, _root: path)

    with pytest.raises(SystemExit, match="rlm nodes not found or empty"):
        rlm_finalize.main(["--ticket", "TK-X", "--no-bootstrap-missing-nodes"])
