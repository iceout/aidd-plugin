from __future__ import annotations

import json
from pathlib import Path

from aidd_runtime import active_state, feature_ids


def _ensure_aidd_docs(tmp_path: Path) -> Path:
    root = tmp_path / "workspace" / "aidd"
    (root / "docs").mkdir(parents=True, exist_ok=True)
    return root


def test_normalize_review_id_keeps_current_iteration() -> None:
    normalized, report_id = active_state.normalize_work_item_for_stage(
        stage="review",
        requested_work_item="id=review:report-42",
        current_work_item="iteration_id=I7",
    )
    assert normalized == "iteration_id=I7"
    assert report_id == "review:report-42"


def test_write_active_state_stores_last_review_report_id(tmp_path: Path) -> None:
    root = _ensure_aidd_docs(tmp_path)

    feature_ids.write_active_state(
        root, ticket="DEMO-1", stage="review", work_item="iteration_id=I1"
    )
    feature_ids.write_active_state(root, stage="review", work_item="id=review:report-99")

    payload = json.loads((root / "docs" / ".active.json").read_text(encoding="utf-8"))
    assert payload.get("work_item") == "iteration_id=I1"
    assert payload.get("last_review_report_id") == "review:report-99"


def test_write_identifiers_normalizes_slug_token_from_note(tmp_path: Path) -> None:
    root = _ensure_aidd_docs(tmp_path)

    feature_ids.write_identifiers(
        root,
        ticket="TST-001",
        slug_hint="tst-001-demo Audit backend workflow determinism",
        scaffold_prd_file=False,
    )
    payload = json.loads((root / "docs" / ".active.json").read_text(encoding="utf-8"))
    assert payload.get("slug_hint") == "tst-001-demo"


def test_iteration_work_item_allows_i_and_m_prefixes() -> None:
    assert active_state.is_iteration_work_item_key("iteration_id=I1")
    assert active_state.is_iteration_work_item_key("iteration_id=M4")
