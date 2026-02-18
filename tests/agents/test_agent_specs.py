from __future__ import annotations

from pathlib import Path


EXPECTED_AGENTS = (
    "analyst.md",
    "researcher.md",
    "planner.md",
    "validator.md",
    "prd-reviewer.md",
    "plan-reviewer.md",
    "spec-interview-writer.md",
    "tasklist-refiner.md",
    "implementer.md",
    "reviewer.md",
    "qa.md",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_all_expected_agents_exist() -> None:
    agents_dir = _repo_root() / "agents"
    assert agents_dir.is_dir()
    existing = sorted(path.name for path in agents_dir.glob("*.md"))
    assert existing == sorted(EXPECTED_AGENTS)


def test_agent_schema_sections() -> None:
    agents_dir = _repo_root() / "agents"
    for file_name in EXPECTED_AGENTS:
        content = (agents_dir / file_name).read_text(encoding="utf-8")
        assert content.startswith("---\n"), f"{file_name}: missing front matter start"
        assert "\n---\n" in content, f"{file_name}: missing front matter end"
        assert "<role>" in content and "</role>" in content, f"{file_name}: missing <role>"
        assert "<process>" in content and "</process>" in content, f"{file_name}: missing <process>"
        assert "<output>" in content and "</output>" in content, f"{file_name}: missing <output>"


def test_agent_specs_do_not_use_legacy_plugin_var() -> None:
    agents_dir = _repo_root() / "agents"
    for file_name in EXPECTED_AGENTS:
        content = (agents_dir / file_name).read_text(encoding="utf-8")
        assert "PLUGIN_DIR" not in content, f"{file_name}: contains deprecated plugin root env var"
