from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from aidd_runtime import ide_profiles


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    cwd: Path
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    stdout_truncated: bool = False
    stderr_truncated: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def build_runtime_env(
    plugin_root: Path,
    *,
    profile: str | ide_profiles.IdeProfile | None = None,
    base_env: Mapping[str, str] | None = None,
    extra_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    profile_cfg = ide_profiles.resolve_profile(profile)
    env = dict(base_env or os.environ)
    discovered_skills_dirs = ide_profiles.discover_skills_dirs(
        profile_cfg,
        env=env,
        include_missing=False,
    )
    if not discovered_skills_dirs:
        discovered_skills_dirs = ide_profiles.discover_skills_dirs(
            profile_cfg,
            env=env,
            include_missing=True,
        )

    env["AIDD_ROOT"] = str(plugin_root)
    env["AIDD_IDE_PROFILE"] = profile_cfg.name
    env["AIDD_SKILLS_DIRS"] = ide_profiles.format_skills_dirs(discovered_skills_dirs)
    if discovered_skills_dirs:
        env["AIDD_PRIMARY_SKILLS_DIR"] = str(discovered_skills_dirs[0])
    env.update(ide_profiles.profile_env_overrides(profile_cfg))
    if extra_env:
        env.update(extra_env)
    return env


def run_command(
    command: Sequence[str],
    *,
    cwd: Path,
    profile: str | ide_profiles.IdeProfile | None = None,
    env: Mapping[str, str] | None = None,
    timeout_sec: float | None = None,
    max_stdout_bytes: int | None = None,
    max_stderr_bytes: int | None = None,
    check: bool = False,
    error_context: str | None = None,
) -> CommandResult:
    profile_cfg = ide_profiles.resolve_profile(profile)
    effective_timeout = timeout_sec if timeout_sec is not None else float(profile_cfg.timeout_sec)
    stdout_limit = (
        max_stdout_bytes if max_stdout_bytes is not None else profile_cfg.max_stdout_bytes
    )
    stderr_limit = (
        max_stderr_bytes if max_stderr_bytes is not None else profile_cfg.max_stderr_bytes
    )

    timed_out = False
    stdout_text = ""
    stderr_text = ""
    returncode = 0
    try:
        proc = subprocess.run(
            list(command),
            cwd=cwd,
            env=dict(env) if env is not None else None,
            text=True,
            capture_output=True,
            check=False,
            timeout=effective_timeout,
        )
        returncode = proc.returncode
        stdout_text = proc.stdout or ""
        stderr_text = proc.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = 124
        stdout_text = _normalize_timeout_output(exc.stdout)
        base_stderr = _normalize_timeout_output(exc.stderr)
        timeout_msg = f"[aidd] ERROR: command timed out after {effective_timeout:.3f}s"
        stderr_text = f"{base_stderr}\n{timeout_msg}".strip()

    stdout_text, stdout_truncated = _truncate_output(stdout_text, stdout_limit)
    stderr_text, stderr_truncated = _truncate_output(stderr_text, stderr_limit)
    result = CommandResult(
        command=tuple(str(part) for part in command),
        cwd=cwd,
        returncode=returncode,
        stdout=stdout_text,
        stderr=stderr_text,
        timed_out=timed_out,
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
    )
    if check and not result.ok:
        summary = (result.stderr or result.stdout or "").strip()
        if error_context:
            raise RuntimeError(f"{error_context}: {summary}")
        raise RuntimeError(summary)
    return result


def run_python(
    script_path: Path,
    *,
    argv: Sequence[str] | None = None,
    cwd: Path,
    profile: str | ide_profiles.IdeProfile | None = None,
    env: Mapping[str, str] | None = None,
    timeout_sec: float | None = None,
    max_stdout_bytes: int | None = None,
    max_stderr_bytes: int | None = None,
    check: bool = False,
    error_context: str | None = None,
) -> CommandResult:
    command = [sys.executable, str(script_path), *(argv or ())]
    return run_command(
        command,
        cwd=cwd,
        profile=profile,
        env=env,
        timeout_sec=timeout_sec,
        max_stdout_bytes=max_stdout_bytes,
        max_stderr_bytes=max_stderr_bytes,
        check=check,
        error_context=error_context,
    )


def _normalize_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _truncate_output(text: str, max_bytes: int) -> tuple[str, bool]:
    if max_bytes <= 0:
        return "", bool(text)
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return text, False
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    suffix = f"\n[aidd] output truncated to {max_bytes} bytes."
    return f"{truncated.rstrip()}{suffix}", True
