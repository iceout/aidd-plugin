from __future__ import annotations


def _bootstrap_entrypoint() -> None:
    import os
    import sys
    from pathlib import Path

    raw_root = os.environ.get("AIDD_ROOT", "").strip()
    plugin_root = None
    if raw_root:
        candidate = Path(raw_root).expanduser()
        if candidate.exists() and (candidate / "aidd_runtime").is_dir():
            plugin_root = candidate.resolve()

    if plugin_root is None:
        current = Path(__file__).resolve()
        for parent in (current.parent, *current.parents):
            if (parent / "aidd_runtime").is_dir():
                plugin_root = parent
                break

    if plugin_root is None:
        raise RuntimeError("Unable to resolve AIDD_ROOT from entrypoint path.")

    os.environ["AIDD_ROOT"] = str(plugin_root)
    plugin_root_str = str(plugin_root)
    if plugin_root_str not in sys.path:
        sys.path.insert(0, plugin_root_str)


_bootstrap_entrypoint()

import argparse
import shutil
import sys
from pathlib import Path

from aidd_runtime.resources import DEFAULT_PROJECT_SUBDIR, resolve_project_root
from aidd_runtime.runtime import require_plugin_root


def _format_status(ok: bool) -> str:
    return "OK" if ok else "MISSING"


def _check_binary(name: str) -> tuple[bool, str]:
    path = shutil.which(name)
    return (path is not None), (path or "not found in PATH")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AIDD install diagnostics.")
    parser.parse_args(argv)

    errors: list[str] = []
    rows: list[tuple[str, bool, str]] = []

    try:
        plugin_root = require_plugin_root()
        rows.append(("AIDD_ROOT", True, str(plugin_root)))
    except RuntimeError as exc:
        rows.append(("AIDD_ROOT", False, str(exc)))
        errors.append("Set AIDD_ROOT to the plugin install path.")
        plugin_root = None

    py_ok = sys.version_info >= (3, 10)
    rows.append(("python3 (>=3.10)", py_ok, sys.executable))
    if not py_ok:
        errors.append("Upgrade Python to 3.10+ and re-run.")

    for binary in ("rg", "git"):
        ok, detail = _check_binary(binary)
        rows.append((binary, ok, detail))
        if not ok:
            errors.append(f"Install `{binary}` and ensure it is on PATH.")

    if plugin_root:
        missing = []
        # Keep this in sync with the current repository/plugin layout.
        for name in ("skills", "aidd_runtime", "agents", "hooks", "templates"):
            if not (plugin_root / name).exists():
                missing.append(name)
        rows.append(
            (
                "plugin layout",
                not missing,
                "missing: " + ", ".join(missing) if missing else "ok",
            )
        )
        if missing:
            errors.append("Reinstall the plugin to restore missing directories.")

    target = Path.cwd().resolve()
    workspace_root, project_root = resolve_project_root(target, DEFAULT_PROJECT_SUBDIR)
    rows.append(("workspace root", workspace_root.exists(), str(workspace_root)))
    if not workspace_root.exists():
        errors.append(f"Workspace root does not exist: {workspace_root}.")

    running_from_plugin_repo = bool(
        plugin_root
        and workspace_root == plugin_root
        and (plugin_root / ".aidd-plugin").exists()
    )
    if running_from_plugin_repo:
        rows.append(
            (
                f"{DEFAULT_PROJECT_SUBDIR}/docs",
                True,
                "skipped (running from plugin repository root; check from a target project workspace)",
            )
        )
    else:
        docs_ok = project_root.exists() and (project_root / "docs").exists()
        rows.append((f"{DEFAULT_PROJECT_SUBDIR}/docs", docs_ok, str(project_root)))
        if not docs_ok:
            errors.append(
                "Run /feature-dev-aidd:aidd-init or "
                "'python3 ${AIDD_ROOT}/skills/aidd-init/runtime/init.py' from the workspace root to bootstrap."
            )
        else:
            critical = [
                "AGENTS.md",
                "docs/shared/stage-lexicon.md",
                "docs/loops/template.loop-pack.md",
                "docs/tasklist/template.md",
            ]
            for rel in critical:
                target = project_root / rel
                ok = target.exists()
                rows.append((f"{DEFAULT_PROJECT_SUBDIR}/{rel}", ok, str(target)))
                if not ok:
                    errors.append(f"Missing critical artifact: {target}")

    print("AIDD Doctor")
    for name, ok, detail in rows:
        print(f"- {name}: {_format_status(ok)} ({detail})")

    if errors:
        print("\nFix:")
        for item in errors:
            print(f"- {item}")
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
