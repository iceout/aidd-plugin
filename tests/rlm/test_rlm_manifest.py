from __future__ import annotations

import json
from pathlib import Path

from aidd_runtime import rlm_manifest


def test_build_manifest_keeps_markdown_targets(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    target = workspace_root / "aidd"
    target.mkdir(parents=True, exist_ok=True)

    (workspace_root / "AGENTS.md").write_text("# Workspace AGENTS\n", encoding="utf-8")
    (target / "AGENTS.md").write_text("# AIDD AGENTS\n", encoding="utf-8")

    targets_path = target / "reports" / "research" / "DOCS-001-rlm-targets.json"
    targets_path.parent.mkdir(parents=True, exist_ok=True)
    targets_path.write_text(
        json.dumps(
            {
                "schema": "aidd.rlm_targets.v1",
                "ticket": "DOCS-001",
                "slug": "docs-001",
                "paths_base": "workspace",
                "files": ["AGENTS.md", "aidd/AGENTS.md"],
            }
        ),
        encoding="utf-8",
    )

    manifest = rlm_manifest.build_manifest(
        target,
        "DOCS-001",
        settings={"max_file_bytes": 0},
        targets_path=targets_path,
        base_root=workspace_root,
    )

    assert [item["path"] for item in manifest["files"]] == ["AGENTS.md", "aidd/AGENTS.md"]
    assert {item["lang"] for item in manifest["files"]} == {"md"}
    assert manifest["stats"]["files_total"] == 2
