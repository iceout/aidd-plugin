#!/usr/bin/env python3
"""Default format-and-test hook used by QA fallback commands.

This script is intentionally conservative:
- Prefer project-provided test entrypoints when available.
- Avoid hard failures when no runnable test command exists.
- Emit "no tests to run" markers so QA can record skipped status.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

LOG_PREFIX = "[format-and-test]"
SKIP_MESSAGE = "no tests to run"


def _echo(message: str) -> None:
    print(f"{LOG_PREFIX} {message}")


def _detect_workspace_root(cwd: Path) -> Path:
    # QA often runs in "<workspace>/aidd". Jump to workspace root for test commands.
    if cwd.name == "aidd" and (cwd / "docs").exists() and cwd.parent.exists():
        return cwd.parent
    return cwd


def _python_tests_present(root: Path) -> bool:
    if (root / "tests").exists() or (root / "pytest.ini").exists():
        return True
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return False
    try:
        text = pyproject.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return "pytest" in text or "tool.pytest" in text


def _pytest_available() -> bool:
    proc = subprocess.run(
        [sys.executable, "-c", "import pytest"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.returncode == 0


def _build_candidates(workspace_root: Path) -> list[list[str]]:
    candidates: list[list[str]] = []

    script_test = workspace_root / "scripts" / "test.sh"
    if script_test.is_file():
        candidates.append(["bash", "scripts/test.sh"])

    if (workspace_root / "Makefile").is_file() and shutil.which("make"):
        candidates.append(["make", "test"])

    if _python_tests_present(workspace_root) and _pytest_available():
        candidates.append([sys.executable, "-m", "pytest"])

    if (workspace_root / "package.json").is_file() and shutil.which("npm"):
        candidates.append(["npm", "test"])

    return candidates


def _run_command(cmd: list[str], cwd: Path) -> int:
    _echo(f"running: {' '.join(cmd)} (cwd={cwd})")
    try:
        proc = subprocess.run(cmd, cwd=cwd, check=False)
    except FileNotFoundError:
        _echo(f"{SKIP_MESSAGE} (missing executable: {cmd[0]})")
        return 0
    return proc.returncode


def main() -> int:
    workspace_root = _detect_workspace_root(Path.cwd().resolve())
    commands = _build_candidates(workspace_root)
    if not commands:
        _echo(SKIP_MESSAGE)
        return 0

    # Run the first project-specific candidate only.
    return _run_command(commands[0], workspace_root)


if __name__ == "__main__":
    raise SystemExit(main())
