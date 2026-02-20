from __future__ import annotations

from pathlib import Path

from aidd_runtime import tasklist_validate


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _base_tasklist_text(*, status: str = "IN_PROGRESS", qa_status: str = "met") -> str:
    return "\n".join(
        [
            "---",
            f"Status: {status}",
            "Plan: docs/plan/TK-1.md",
            "PRD: docs/prd/TK-1.prd.md",
            "Spec: docs/spec/TK-1.spec.yaml",
            "---",
            "## AIDD:CONTEXT_PACK",
            "- Stage: implement",
            f"- Status: {status}",
            "## AIDD:SPEC_PACK",
            "- spec ready",
            "## AIDD:TEST_STRATEGY",
            "- smoke tests",
            "## AIDD:TEST_EXECUTION",
            "- profile: default",
            "- tasks: unit",
            "- filters: none",
            "- when: pre-commit",
            "- reason: guardrail",
            "## AIDD:ITERATIONS_FULL",
            "- [ ] Build API (iteration_id: I1) (priority: high) (blocking: false)",
            "  - State: open",
            "  - Steps:",
            "    - step 1",
            "    - step 2",
            "    - step 3",
            "  - Expected paths:",
            "    - src/api.py",
            "  - Size budget:",
            "    - max_files: 3",
            "    - max_loc: 120",
            "  - DoD: done",
            "  - Boundaries: stay in API layer",
            "  - Tests: pytest -k api",
            "## AIDD:NEXT_3",
            "- [ ] Build API (ref: iteration_id=I1)",
            "- [ ] QA follow-up (ref: id=H1)",
            "## AIDD:HANDOFF_INBOX",
            "- [ ] QA follow-up (id: H1) (source: qa) (priority: medium) (blocking: false)",
            "  - Status: open",
            "  - DoD: sync QA report",
            "  - Boundaries: docs only",
            "  - Tests: pytest -k smoke",
            "## AIDD:QA_TRACEABILITY",
            f"- AC-1 -> check -> {qa_status} -> aidd/reports/tests.log",
            "## AIDD:CHECKLIST",
            "### AIDD:CHECKLIST_QA",
            "- [ ] acceptance reviewed",
            "## AIDD:PROGRESS_LOG",
            "- (empty)",
            "## AIDD:HOW_TO_UPDATE",
            "- Keep sections aligned with plan and QA artifacts.",
            "",
        ]
    )


def test_check_tasklist_text_reports_missing_sections(tmp_path: Path) -> None:
    root = tmp_path / "aidd"
    text = "\n".join(
        [
            "---",
            "Status: IN_PROGRESS",
            "---",
            "## AIDD:CONTEXT_PACK",
            "- Stage: implement",
            "- Status: IN_PROGRESS",
        ]
    )
    result = tasklist_validate.check_tasklist_text(root, "TK-1", text)
    assert result.status == "error"
    assert result.details is not None
    assert any("missing section: ## AIDD:ITERATIONS_FULL" in item for item in result.details)


def test_check_tasklist_text_flags_ready_with_not_met_traceability(tmp_path: Path) -> None:
    root = tmp_path / "aidd"
    _write(
        root / "docs" / "plan" / "TK-1.md",
        "\n".join(["## AIDD:ITERATIONS", "- Build API (iteration_id: I1)"]),
    )
    _write(root / "docs" / "prd" / "TK-1.prd.md", "## AIDD:GOALS\n- backend change")
    _write(root / "docs" / "spec" / "TK-1.spec.yaml", "version: 1\n")

    text = _base_tasklist_text(status="READY", qa_status="not-met")
    result = tasklist_validate.check_tasklist_text(root, "TK-1", text)
    assert result.status == "error"
    assert result.details is not None
    assert any("Status READY with QA_TRACEABILITY NOT MET" in item for item in result.details)
