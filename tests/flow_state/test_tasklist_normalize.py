from __future__ import annotations

from pathlib import Path

from aidd_runtime import tasklist_check as core
from aidd_runtime import tasklist_normalize as normalize


def _iteration(
    *,
    item_id: str,
    checkbox: str = "open",
    state: str = "open",
    priority: str = "medium",
    blocking: bool = False,
    deps: list[str] | None = None,
) -> core.IterationItem:
    return core.IterationItem(
        item_id=item_id,
        title=f"title-{item_id}",
        state=state,
        checkbox=checkbox,
        parent_id=None,
        explicit_id=True,
        priority=priority,
        blocking=blocking,
        deps=list(deps or []),
        locks=[],
        lines=[f"- [ ] item ({item_id})"],
    )


def _handoff(
    *,
    item_id: str,
    checkbox: str = "open",
    status: str = "open",
    priority: str = "medium",
    blocking: bool = False,
    source: str = "qa",
) -> core.HandoffItem:
    return core.HandoffItem(
        item_id=item_id,
        title=f"handoff-{item_id}",
        status=status,
        checkbox=checkbox,
        priority=priority,
        blocking=blocking,
        source=source,
        lines=[f"- [ ] handoff ({item_id})"],
    )


def test_deps_resolution_and_open_item_sorting() -> None:
    done = _iteration(item_id="I0", checkbox="done", state="done")
    blocked = _iteration(
        item_id="I1",
        checkbox="open",
        state="open",
        priority="critical",
        blocking=True,
        deps=["iteration_id=I0"],
    )
    normal = _iteration(item_id="I2", checkbox="open", state="open", priority="high")
    unmet = _iteration(item_id="I3", checkbox="open", state="open", deps=["I404"])
    handoff = _handoff(item_id="H1", priority="high")

    assert normalize.deps_satisfied(["I0"], {"I0": done}, {}) is True
    assert normalize.deps_satisfied(["I404"], {"I0": done}, {}) is False
    assert normalize.unmet_deps(["I0", "I404"], {"I0": done}, {}) == ["I404"]

    open_items, _, _ = normalize.build_open_items(
        [done, blocked, normal, unmet],
        [handoff],
        plan_order=["I1", "I2", "I3"],
    )
    assert [item.item_id for item in open_items] == ["I1", "H1", "I2"]


def test_normalize_progress_section_dedup_and_archive(tmp_path: Path) -> None:
    root = tmp_path / "aidd"
    root.mkdir()
    summary: list[str] = []
    lines = [
        "## AIDD:PROGRESS_LOG",
        "intro",
        "- 2026-02-20 source=implement id=I1 kind=iteration hash=abc msg=done",
        "- 2026-02-20 source=implement id=I1 kind=iteration hash=abc msg=done",
        "- invalid line",
    ]

    dry_lines = normalize.normalize_progress_section(
        lines,
        "TK-1",
        root,
        summary,
        dry_run=True,
    )
    assert dry_lines[0] == "## AIDD:PROGRESS_LOG"
    assert any("deduped 1 progress entries" in item for item in summary)
    assert any("dropped 1 invalid progress entries" in item for item in summary)

    summary.clear()
    written_lines = normalize.normalize_progress_section(
        lines,
        "TK-1",
        root,
        summary,
        dry_run=False,
    )
    archive = root / "reports" / "progress" / "TK-1.log"
    assert archive.exists()
    assert "source=implement id=I1" in archive.read_text(encoding="utf-8")
    assert any("archived 1 progress entries" in item for item in summary)
    assert written_lines[0] == "## AIDD:PROGRESS_LOG"


def test_normalize_qa_traceability_and_defaults() -> None:
    summary: list[str] = []
    lines = [
        "## AIDD:QA_TRACEABILITY",
        "- AC-1 → check → met → report-a",
        "- AC-1 → check → not-met → report-b",
        "- AC-2 → check → met → report-c",
    ]
    merged = normalize.normalize_qa_traceability(lines, summary)

    assert merged[0] == "## AIDD:QA_TRACEABILITY"
    assert any(
        "AC-1" in line and "not-met" in line and "report-a; report-b" in line for line in merged
    )
    assert any("merged 2 QA traceability entries" in item for item in summary)

    fallback = normalize.normalize_qa_traceability(["## AIDD:QA_TRACEABILITY"], [])
    assert fallback[-1] == "- AC-1 -> <check> -> met -> <evidence>"


def test_normalize_handoff_section_merges_by_source_and_injects_manual_block() -> None:
    summary: list[str] = []
    section_a = core.Section(
        title="AIDD:HANDOFF_INBOX",
        start=0,
        end=0,
        lines=[
            "## AIDD:HANDOFF_INBOX",
            "preface",
            "<!-- handoff:qa start -->",
            "- [ ] qa open (id: H1)",
            "  - source: qa",
            "<!-- handoff:qa end -->",
            "- [ ] manual task (id: HM1)",
            "  - source: manual",
        ],
    )
    section_b = core.Section(
        title="AIDD:HANDOFF_INBOX",
        start=0,
        end=0,
        lines=[
            "## AIDD:HANDOFF_INBOX",
            "<!-- handoff:qa start -->",
            "- [x] qa done (id: H1)",
            "  - source: reviewer",
            "<!-- handoff:qa end -->",
        ],
    )

    merged = normalize.normalize_handoff_section([section_a, section_b], summary)
    assert merged[0] == "## AIDD:HANDOFF_INBOX"
    assert "<!-- handoff:manual start -->" in merged
    assert "<!-- handoff:manual end -->" in merged
    assert any("source: review" in line for line in merged)
    assert any("deduped 1 handoff task(s)" in item for item in summary)


def test_normalize_tasklist_rebuilds_next3(tmp_path: Path) -> None:
    root = tmp_path / "aidd"
    plan_path = root / "docs" / "plan" / "TK-2.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "\n".join(
            [
                "## AIDD:ITERATIONS",
                "- item (iteration_id: I1)",
            ]
        ),
        encoding="utf-8",
    )

    text = "\n".join(
        [
            "## AIDD:ITERATIONS_FULL",
            "- [ ] Build (iteration_id: I1) (priority: high)",
            "  - State: open",
            "## AIDD:NEXT_3",
            "- (none) no pending items",
            "## AIDD:HANDOFF_INBOX",
            "<!-- handoff:manual start -->",
            "<!-- handoff:manual end -->",
        ]
    )
    result = normalize.normalize_tasklist(root, "TK-2", text, dry_run=True)
    assert result.changed is True
    assert "rebuilt AIDD:NEXT_3" in result.summary
    assert "(ref: iteration_id=I1)" in result.updated_text
