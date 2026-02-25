from __future__ import annotations

from pathlib import Path


def _bootstrap_missing_os_import(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    marker = "def _bootstrap_entrypoint() -> None:"
    start = text.find(marker)
    if start < 0:
        return False

    end = text.find("_bootstrap_entrypoint()", start + len(marker))
    block = text[start : end if end >= 0 else None]
    os_use = block.find('raw_root = os.environ.get("AIDD_ROOT", "").strip()')
    if os_use < 0:
        return False

    # `import os` must be visible before use: either at module top (before function def)
    # or inside `_bootstrap_entrypoint()` before the first `os.environ` access.
    before_use_in_func = block[:os_use]
    before_func = text[:start]
    return "import os" not in before_use_in_func and "import os" not in before_func


def test_bootstrap_entrypoints_import_os_before_use() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    candidates = sorted(
        {
            *repo_root.joinpath("skills").rglob("*.py"),
            *repo_root.joinpath("aidd_runtime").rglob("*.py"),
        }
    )

    bad = [str(path.relative_to(repo_root)) for path in candidates if _bootstrap_missing_os_import(path)]
    assert bad == [], f"_bootstrap_entrypoint() uses os.environ before importing os: {bad}"
