#!/usr/bin/env python3
"""Deprecated compatibility wrapper for the old researcher_context CLI.

The legacy context/targets flow was removed in favor of RLM-only research
artifacts. This module now forwards execution to the canonical stage entrypoint:
`skills/researcher/runtime/research.py`.
"""

from __future__ import annotations

import sys

from aidd_runtime import research as research_runtime


def main(argv: list[str] | None = None) -> int:
    print(
        "[aidd] WARN: researcher_context.py is deprecated; forwarding to researcher/runtime/research.py (RLM-only).",
        file=sys.stderr,
    )
    return research_runtime.main(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
