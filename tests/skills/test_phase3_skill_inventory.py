from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_phase3_stage_and_shared_skills_exist() -> None:
    required_skills = [
        "idea-new",
        "plan-new",
        "tasks-new",
        "researcher",
        "implement",
        "review",
        "qa",
        "review-spec",
        "spec-interview",
        "aidd-policy",
        "aidd-reference",
        "aidd-stage-research",
    ]
    for skill in required_skills:
        skill_md = PROJECT_ROOT / "skills" / skill / "SKILL.md"
        assert skill_md.exists(), f"missing SKILL.md: {skill_md}"


def test_legacy_flow_skills_are_migration_shims() -> None:
    legacy_flows = [
        "aidd-idea-flow",
        "aidd-research-flow",
        "aidd-plan-flow",
        "aidd-implement-flow",
        "aidd-review-flow",
        "aidd-qa-flow",
    ]
    for flow in legacy_flows:
        text = (PROJECT_ROOT / "skills" / flow / "SKILL.md").read_text(encoding="utf-8")
        assert "Legacy Flow Compatibility" in text
