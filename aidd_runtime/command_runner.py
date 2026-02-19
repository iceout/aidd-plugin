from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    cwd: Path
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def build_runtime_env(
    plugin_root: Path,
    *,
    base_env: Mapping[str, str] | None = None,
    extra_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    env = dict(base_env or os.environ)
    env["AIDD_ROOT"] = str(plugin_root)
    if extra_env:
        env.update(extra_env)
    return env


def run_command(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    check: bool = False,
    error_context: str | None = None,
) -> CommandResult:
    proc = subprocess.run(
        list(command),
        cwd=cwd,
        env=dict(env) if env is not None else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = CommandResult(
        command=tuple(str(part) for part in command),
        cwd=cwd,
        returncode=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
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
    env: Mapping[str, str] | None = None,
    check: bool = False,
    error_context: str | None = None,
) -> CommandResult:
    command = [sys.executable, str(script_path), *(argv or ())]
    return run_command(
        command,
        cwd=cwd,
        env=env,
        check=check,
        error_context=error_context,
    )
