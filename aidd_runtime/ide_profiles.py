from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IdeProfile:
    name: str
    command_leaders: tuple[str, ...]
    command_namespaces: tuple[str, ...]
    skills_dirs: tuple[str, ...]
    timeout_sec: int
    max_stdout_bytes: int
    max_stderr_bytes: int
    permission_mode: str
    env_overrides: tuple[tuple[str, str], ...] = ()


DEFAULT_PROFILE = "kimi"

PROFILES: dict[str, IdeProfile] = {
    "kimi": IdeProfile(
        name="kimi",
        command_leaders=("/",),
        command_namespaces=("skill", "flow", "feature-dev-aidd", "aidd"),
        skills_dirs=("~/.config/agents/skills",),
        timeout_sec=180,
        max_stdout_bytes=50_000,
        max_stderr_bytes=20_000,
        permission_mode="default",
        env_overrides=(("AIDD_HOST", "kimi"),),
    ),
    "codex": IdeProfile(
        name="codex",
        command_leaders=("$", "/"),
        command_namespaces=("aidd", "skill", "flow", "feature-dev-aidd"),
        skills_dirs=("~/.codex/skills",),
        timeout_sec=180,
        max_stdout_bytes=50_000,
        max_stderr_bytes=20_000,
        permission_mode="default",
        env_overrides=(("AIDD_HOST", "codex"),),
    ),
    "cursor": IdeProfile(
        name="cursor",
        command_leaders=("/",),
        command_namespaces=("aidd", "skill", "flow", "feature-dev-aidd"),
        skills_dirs=("~/.cursor/skills",),
        timeout_sec=180,
        max_stdout_bytes=50_000,
        max_stderr_bytes=20_000,
        permission_mode="default",
        env_overrides=(("AIDD_HOST", "cursor"),),
    ),
}


def normalize_profile_name(value: str | None) -> str:
    return str(value or "").strip().lower().replace("_", "-")


def supported_profiles() -> tuple[str, ...]:
    return tuple(sorted(PROFILES))


def resolve_profile(profile: str | IdeProfile | None = None) -> IdeProfile:
    if isinstance(profile, IdeProfile):
        return profile
    if profile is None:
        profile_name = normalize_profile_name(os.getenv("AIDD_IDE_PROFILE", "")) or DEFAULT_PROFILE
    else:
        profile_name = normalize_profile_name(profile)
    resolved = PROFILES.get(profile_name)
    if resolved is None:
        supported = ", ".join(supported_profiles())
        raise ValueError(f"unsupported ide profile '{profile_name}'. Supported: {supported}")
    return resolved


def profile_env_overrides(profile: IdeProfile) -> dict[str, str]:
    return dict(profile.env_overrides)


def profile_skills_dirs(profile: IdeProfile) -> tuple[Path, ...]:
    return tuple(Path(path).expanduser() for path in profile.skills_dirs)


def discover_skills_dirs(
    profile: IdeProfile,
    *,
    env: Mapping[str, str] | None = None,
    include_missing: bool = False,
    allow_env_override: bool = True,
) -> tuple[Path, ...]:
    env_map = env or os.environ
    if allow_env_override:
        overridden = parse_skills_dirs(env_map.get("AIDD_SKILLS_DIRS"))
        if overridden:
            return _filter_skills_dirs(overridden, include_missing=include_missing)
    return _filter_skills_dirs(profile_skills_dirs(profile), include_missing=include_missing)


def parse_skills_dirs(raw_value: str | None) -> tuple[Path, ...]:
    raw = str(raw_value or "").strip()
    if not raw:
        return ()
    parts = [part.strip() for part in raw.split(os.pathsep)]
    paths = [Path(part).expanduser() for part in parts if part]
    return tuple(_dedupe_paths(paths))


def format_skills_dirs(paths: Sequence[Path]) -> str:
    return os.pathsep.join(str(path) for path in paths)


def select_profile(
    command: str,
    *,
    profile: str | IdeProfile | None = None,
    env: Mapping[str, str] | None = None,
) -> IdeProfile:
    if profile is not None:
        return resolve_profile(profile)

    env_map = env or os.environ
    from_command = detect_profile_from_command(command)
    if from_command is not None:
        return from_command

    from_env = _resolve_env_profile(env_map)
    if from_env is not None:
        return from_env

    detected = detect_profiles_from_skills_dirs(env=env_map)
    if len(detected) == 1:
        return detected[0]

    return PROFILES[DEFAULT_PROFILE]


def detect_profile_from_command(command: str) -> IdeProfile | None:
    text = (command or "").lstrip()
    if text.startswith("$"):
        return PROFILES["codex"]
    return None


def detect_profiles_from_skills_dirs(
    *,
    env: Mapping[str, str] | None = None,
) -> tuple[IdeProfile, ...]:
    env_map = env or os.environ
    detected: list[IdeProfile] = []
    for profile in PROFILES.values():
        if _profile_has_installed_skills(profile, env=env_map):
            detected.append(profile)
    return tuple(detected)


def strip_host_prefix(command: str, profile: IdeProfile) -> str:
    raw = (command or "").strip()
    if not raw:
        return ""

    stripped = raw
    for leader in profile.command_leaders:
        if stripped.startswith(leader):
            stripped = stripped[len(leader) :].strip()
            break

    if ":" in stripped:
        prefix, suffix = stripped.split(":", 1)
        if normalize_profile_name(prefix) in profile.command_namespaces:
            return suffix.strip()
    parts = stripped.split(None, 1)
    if len(parts) == 2 and normalize_profile_name(parts[0]) in profile.command_namespaces:
        return parts[1].strip()
    return stripped


def _resolve_env_profile(env: Mapping[str, str]) -> IdeProfile | None:
    profile_name = normalize_profile_name(env.get("AIDD_IDE_PROFILE"))
    if profile_name in PROFILES:
        return PROFILES[profile_name]
    host_name = normalize_profile_name(env.get("AIDD_HOST"))
    if host_name in PROFILES:
        return PROFILES[host_name]
    return None


def _profile_has_installed_skills(profile: IdeProfile, *, env: Mapping[str, str]) -> bool:
    for skills_dir in discover_skills_dirs(
        profile,
        env=env,
        include_missing=False,
        allow_env_override=False,
    ):
        if _skills_dir_has_installation(skills_dir):
            return True
    return False


def _skills_dir_has_installation(skills_dir: Path) -> bool:
    if not skills_dir.is_dir():
        return False
    if (skills_dir / "aidd-core" / "SKILL.md").is_file():
        return True
    try:
        for child in skills_dir.iterdir():
            if child.is_dir() and (child / "SKILL.md").is_file():
                return True
    except OSError:
        return False
    return False


def _filter_skills_dirs(paths: Sequence[Path], *, include_missing: bool) -> tuple[Path, ...]:
    deduped = _dedupe_paths(paths)
    if include_missing:
        return tuple(deduped)
    return tuple(path for path in deduped if path.is_dir())


def _dedupe_paths(paths: Sequence[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result
