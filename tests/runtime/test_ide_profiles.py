from __future__ import annotations

from pathlib import Path

import pytest

from aidd_runtime import ide_profiles


def test_strip_host_prefix_codex_style() -> None:
    profile = ide_profiles.resolve_profile("codex")
    assert ide_profiles.strip_host_prefix("$aidd:plan-new", profile) == "plan-new"
    assert ide_profiles.strip_host_prefix("$skill:idea-new", profile) == "idea-new"


def test_strip_host_prefix_cursor_style() -> None:
    profile = ide_profiles.resolve_profile("cursor")
    assert ide_profiles.strip_host_prefix("/aidd:tasks-new", profile) == "tasks-new"
    assert ide_profiles.strip_host_prefix("/flow:aidd-review-flow", profile) == "aidd-review-flow"


def test_resolve_profile_invalid() -> None:
    with pytest.raises(ValueError):
        ide_profiles.resolve_profile("unknown-host")


def test_select_profile_prefers_command_hint_over_env_hint() -> None:
    profile = ide_profiles.select_profile(
        "$aidd:plan-new",
        env={"AIDD_IDE_PROFILE": "cursor"},
    )
    assert profile.name == "codex"


def test_select_profile_uses_env_hint_without_command_signal() -> None:
    profile = ide_profiles.select_profile(
        "/skill:plan-new",
        env={"AIDD_IDE_PROFILE": "cursor"},
    )
    assert profile.name == "cursor"


def test_select_profile_from_command_hint() -> None:
    profile = ide_profiles.select_profile("$aidd:plan-new", env={})
    assert profile.name == "codex"


def test_select_profile_from_single_installed_skills_dir(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    cursor_skill = tmp_path / ".cursor" / "skills" / "aidd-core"
    cursor_skill.mkdir(parents=True, exist_ok=True)
    (cursor_skill / "SKILL.md").write_text("# aidd-core\n", encoding="utf-8")

    profile = ide_profiles.select_profile("plan-new", env={})
    assert profile.name == "cursor"


def test_discover_skills_dirs_honors_env_override(tmp_path: Path) -> None:
    custom_dir = tmp_path / "custom-skills"
    profile = ide_profiles.resolve_profile("kimi")
    dirs = ide_profiles.discover_skills_dirs(
        profile,
        env={"AIDD_SKILLS_DIRS": str(custom_dir)},
        include_missing=True,
    )
    assert dirs == (custom_dir,)
