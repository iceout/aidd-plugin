"""Event logging for workflow status."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aidd_runtime.io_utils import append_jsonl, read_jsonl, utc_timestamp


def events_path(root: Path, ticket: str) -> Path:
    return root / "reports" / "events" / f"{ticket}.jsonl"


def append_event(
    root: Path,
    *,
    ticket: str,
    slug_hint: str | None,
    event_type: str,
    status: str | None = None,
    details: dict[str, Any] | None = None,
    report_path: Path | None = None,
    source: str | None = None,
) -> None:
    if not ticket:
        return
    payload: dict[str, Any] = {
        "ts": utc_timestamp(),
        "ticket": ticket,
        "slug_hint": slug_hint,
        "type": event_type,
    }
    if status:
        payload["status"] = status
    if details:
        payload["details"] = details
    if report_path:
        payload["report"] = report_path.as_posix()
    if source:
        payload["source"] = source

    path = events_path(root, ticket)
    append_jsonl(path, payload)


def read_events(root: Path, ticket: str, *, limit: int = 5) -> list[dict[str, Any]]:
    path = events_path(root, ticket)
    if not path.exists():
        return []
    events = read_jsonl(path)
    if not events:
        return []
    if limit <= 0:
        return []
    return events[-max(limit, 0) :]
