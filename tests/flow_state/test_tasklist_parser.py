from __future__ import annotations

from aidd_runtime import tasklist_check as parser


def test_parse_front_matter_and_sections() -> None:
    lines = [
        "---",
        "Status: IN_PROGRESS",
        "# note",
        "Plan: docs/plan/TK-1.md",
        "---",
        "intro",
        "## NotAidd",
        "x",
        "## AIDD:CONTEXT_PACK",
        "- Stage: implement",
        "## AIDD:TEST_EXECUTION",
        "- profile: default",
    ]

    front, start = parser.parse_front_matter(lines)
    assert front["Status"] == "IN_PROGRESS"
    assert front["Plan"] == "docs/plan/TK-1.md"
    assert start == 5

    sections, section_map = parser.parse_sections(lines)
    assert [section.title for section in sections] == ["AIDD:CONTEXT_PACK", "AIDD:TEST_EXECUTION"]
    assert "NotAidd" not in section_map


def test_parse_sections_accepts_numbered_aidd_headers() -> None:
    lines = [
        "## 7. AIDD:GOALS",
        "- docs-only update",
        "## 8. AIDD:NON_GOALS",
        "- no api changes",
    ]
    sections, section_map = parser.parse_sections(lines)
    assert [section.title for section in sections] == ["AIDD:GOALS", "AIDD:NON_GOALS"]
    assert "AIDD:GOALS" in section_map


def test_extract_section_text_does_not_fallback_to_full_by_default() -> None:
    text = "\n".join(
        [
            "# PRD",
            "Some prose mentioning web/flask_app.py and api endpoint",
            "## Notes",
            "no aidd sections here",
        ]
    )
    extracted = parser.extract_section_text(text, ("AIDD:GOALS", "AIDD:ACCEPTANCE"))
    assert extracted == ""
    assert parser.mentions_spec_required(extracted) is False


def test_parse_iteration_items_supports_inline_and_list_fields() -> None:
    section_lines = [
        "- [ ] I1: Build API (iteration_id: I1) (priority: high) (blocking: true)",
        "  - State: open",
        "  - deps: [iteration_id=I0, id=H1]",
        "  - locks:",
        "    - src/api.py",
        "  - parent_iteration_id: P-1",
        "- [x] I2: done item",
        "  - iteration_id: I2",
        "  - State: done",
        "  - deps:",
        "    - I1",
    ]

    items = parser.parse_iteration_items(section_lines)
    assert [item.item_id for item in items] == ["I1", "I2"]
    assert items[0].checkbox == "open"
    assert items[0].priority == "high"
    assert items[0].blocking is True
    assert items[0].parent_id == "P-1"
    assert items[0].deps == ["I0", "H1"]
    assert items[0].locks == ["src/api.py"]
    assert items[0].explicit_id is True
    assert items[1].checkbox == "done"
    assert items[1].deps == ["I1"]


def test_parse_handoff_and_next3_reference_helpers() -> None:
    handoff_lines = [
        "- [ ] QA follow-up (id: H1) (source: reviewer) (priority: critical) (blocking: true)",
        "  - Status: open",
        "- [x] Docs update (id: H2)",
        "  - source: qa",
    ]
    handoff_items = parser.parse_handoff_items(handoff_lines)

    assert [item.item_id for item in handoff_items] == ["H1", "H2"]
    assert handoff_items[0].source == "review"
    assert handoff_items[0].priority == "critical"
    assert handoff_items[0].blocking is True
    assert handoff_items[1].status == "done"

    next3_lines = [
        "- [ ] first (ref: iteration_id=I1)",
        "- [ ] second",
        "  - id: H2",
    ]
    blocks = parser.parse_next3_items(next3_lines)
    assert len(blocks) == 2
    assert parser.extract_ref_id(blocks[0]) == ("iteration", "I1", True)
    assert parser.extract_ref_id(blocks[1]) == ("handoff", "H2", False)

    assert parser.next3_placeholder_present(["- (none) no pending items"]) is True
    assert parser.next3_placeholder_present(["- [ ] real task"]) is False
