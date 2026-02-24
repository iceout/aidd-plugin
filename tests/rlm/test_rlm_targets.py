from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from aidd_runtime import research_hints
from aidd_runtime import rlm_targets


def test_prefix_and_override_helpers() -> None:
    assert rlm_targets._normalize_prefixes([" ./src/ ", "", "app\\api\\ "]) == ["src", "app/api"]
    assert rlm_targets._filter_prefixes(
        ["src/a.py", "vendor/x.py", "docs/readme.md"], ["vendor"]
    ) == ["src/a.py", "docs/readme.md"]
    assert rlm_targets._include_prefixes(["src/a.py", "vendor/x.py", "src/sub/b.py"], ["src"]) == [
        "src/a.py",
        "src/sub/b.py",
    ]
    assert rlm_targets._parse_override_paths("src,tests:pkg") == ["src", "tests", "pkg"]


def test_parse_files_touched_and_discover_common_paths(tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text(
        "\n".join(
            [
                "## AIDD:FILES_TOUCHED",
                "- `src/app.py` - main logic",
                "- tests/test_app.py — unit tests",
                "## AIDD:OTHER",
                "- ignore",
            ]
        ),
        encoding="utf-8",
    )
    assert rlm_targets._parse_files_touched(plan) == ["src/app.py", "tests/test_app.py"]

    base = tmp_path / "workspace"
    (base / "frontend" / "src").mkdir(parents=True)
    (base / "backend" / "src" / "main").mkdir(parents=True)
    (base / "node_modules" / "pkg" / "src" / "main").mkdir(parents=True)
    discovered = rlm_targets._discover_common_paths(base, ignore_dirs={"node_modules"})
    assert "frontend/src" in discovered
    assert "backend/src/main" in discovered
    assert all(not item.startswith("node_modules/") for item in discovered)


def test_build_targets_orders_keyword_hits_and_applies_filters(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "aidd"
    base_root = tmp_path / "workspace"
    (target / "docs" / "plan").mkdir(parents=True, exist_ok=True)
    base_root.mkdir()

    monkeypatch.setattr(
        rlm_targets,
        "_load_hints",
        lambda _target, _ticket: (
            research_hints.ResearchHints(paths=[], keywords=["Service"], notes=["note-a"]),
            "aidd/docs/prd/TK-1.prd.md#AIDD:RESEARCH_HINTS",
        ),
    )
    monkeypatch.setattr(
        rlm_targets, "_parse_files_touched", lambda _plan: ["src/touched.py", "vendor/x.py"]
    )
    monkeypatch.setattr(
        rlm_targets, "_discover_common_paths", lambda _base, **_kw: ["src", "vendor"]
    )

    roots = [base_root / "src", base_root / "vendor"]
    monkeypatch.setattr(rlm_targets, "_resolve_roots", lambda *_a, **_k: roots)
    monkeypatch.setattr(
        rlm_targets,
        "_walk_files",
        lambda *_a, **_k: ["vendor/x.py", "src/service.py", "src/other.py"],
    )
    monkeypatch.setattr(
        rlm_targets,
        "_rg_files_with_matches",
        lambda *_a, **_k: {"src/service.py"},
    )
    monkeypatch.setattr(
        rlm_targets.runtime,
        "resolve_feature_context",
        lambda *_a, **_k: SimpleNamespace(slug_hint="slug-1"),
    )

    payload = rlm_targets.build_targets(
        target,
        "TK-1",
        settings={"exclude_path_prefixes": ["vendor"], "max_files": 10, "max_file_bytes": 0},
        base_root=base_root,
    )

    assert payload["ticket"] == "TK-1"
    assert payload["slug_hint"] == "slug-1"
    assert payload["targets_mode"] == "auto"
    assert payload["paths_discovered"] == ["src"]
    assert payload["files_touched"] == ["src/touched.py"]
    assert payload["files"][0] == "src/service.py"  # keyword hit ranked first
    assert payload["stats"]["keyword_hits"] == 1


def test_main_writes_targets_payload(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "aidd"
    target.mkdir()
    out = target / "reports" / "research" / "out.json"

    monkeypatch.setattr(rlm_targets.runtime, "require_workflow_root", lambda: (tmp_path, target))
    monkeypatch.setattr(
        rlm_targets.runtime,
        "require_ticket",
        lambda _target, ticket=None, slug_hint=None: ("TK-2", SimpleNamespace(slug_hint="tk-2")),
    )
    monkeypatch.setattr(rlm_targets, "load_rlm_settings", lambda _target: {"targets_mode": "auto"})
    monkeypatch.setattr(
        rlm_targets,
        "build_targets",
        lambda *_a, **_k: {
            "schema": "x",
            "ticket": "TK-2",
            "files": [],
            "stats": {"files_total": 0},
        },
    )
    monkeypatch.setattr(
        rlm_targets.runtime,
        "resolve_path_for_target",
        lambda path, _target: out if path == Path("x.json") else path,
    )
    monkeypatch.setattr(rlm_targets.runtime, "rel_path", lambda path, _target: path.name)

    rc = rlm_targets.main(["--ticket", "TK-2", "--output", "x.json"])
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["ticket"] == "TK-2"
