from __future__ import annotations

import re


def _strip_placeholder(value: str) -> str | None:
    stripped = value.strip()
    if not stripped:
        return None
    if stripped.startswith("<") and stripped.endswith(">"):
        return None
    return stripped


def extract_scalar_field(lines: list[str], field: str) -> str | None:
    pattern = re.compile(rf"^\s*-\s*{re.escape(field)}\s*:\s*(.+)$", re.IGNORECASE)
    for line in lines:
        match = pattern.match(line)
        if match:
            value = match.group(1).strip()
            return _strip_placeholder(value) or value
    return None


def extract_list_field(lines: list[str], field: str) -> list[str]:
    pattern = re.compile(rf"^(?P<indent>\s*)-\s*{re.escape(field)}\s*:\s*$", re.IGNORECASE)
    for idx, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        base_indent = len(match.group("indent"))
        items: list[str] = []
        for raw in lines[idx + 1 :]:
            if not raw.strip():
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            if indent <= base_indent and raw.lstrip().startswith("-"):
                break
            if indent <= base_indent and raw.strip():
                break
            if raw.lstrip().startswith("-") and indent > base_indent:
                item = raw.lstrip()[2:].strip()
                if _strip_placeholder(item):
                    items.append(item)
        return items
    return []


def extract_mapping_field(lines: list[str], field: str) -> dict[str, str]:
    pattern = re.compile(rf"^(?P<indent>\s*)-\s*{re.escape(field)}\s*:\s*$", re.IGNORECASE)
    for idx, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        base_indent = len(match.group("indent"))
        result: dict[str, str] = {}
        for raw in lines[idx + 1 :]:
            if not raw.strip():
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            if indent <= base_indent and raw.lstrip().startswith("-"):
                break
            if indent <= base_indent and raw.strip():
                break
            if raw.lstrip().startswith("-") and indent > base_indent:
                item = raw.lstrip()[2:].strip()
                if ":" in item:
                    key, value = item.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    if _strip_placeholder(key) and _strip_placeholder(value):
                        result[key] = value
        return result
    return {}


PATH_TOKEN_RE = re.compile(
    r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.*/-]+|\b[A-Za-z0-9_.-]+\.[A-Za-z0-9_.-]+\b"
)

SECTION_HEADER_RE = re.compile(r"^##\s+(.+?)\s*$")


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    deduped: list[str] = []
    for item in items:
        key = item.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _strip_task_ticks(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        return text[1:-1].strip()
    return text


def _split_task_commands(raw: str) -> list[str]:
    text = _strip_task_ticks(raw)
    if not text:
        return []

    parts: list[str] = []
    buf: list[str] = []
    in_single = False
    in_double = False
    escape = False
    idx = 0

    def _flush() -> None:
        item = "".join(buf).strip()
        buf.clear()
        if item:
            parts.append(item)

    while idx < len(text):
        ch = text[idx]
        if escape:
            buf.append(ch)
            escape = False
            idx += 1
            continue

        if ch == "\\" and not in_single:
            buf.append(ch)
            escape = True
            idx += 1
            continue

        if ch == "'" and not in_double:
            in_single = not in_single
            buf.append(ch)
            idx += 1
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            buf.append(ch)
            idx += 1
            continue

        if not in_single and not in_double:
            if ch == ";":
                _flush()
                idx += 1
                continue
            if ch == "&" and idx + 1 < len(text) and text[idx + 1] == "&":
                _flush()
                idx += 2
                continue

        buf.append(ch)
        idx += 1

    _flush()
    return parts


def _extract_paths_from_brackets(text: str) -> list[str]:
    results: list[str] = []
    for match in re.findall(r"\[([^\]]+)\]", text):
        parts = re.split(r"[,\n]", match)
        for part in parts:
            cleaned = part.strip().strip("`'\" ")
            if cleaned:
                results.append(cleaned)
    return results


def _extract_paths_from_text(text: str) -> list[str]:
    candidates: list[str] = []
    candidates.extend(_extract_paths_from_brackets(text))
    for match in PATH_TOKEN_RE.findall(text):
        cleaned = match.strip().strip("`'\" ,;)")
        if cleaned:
            candidates.append(cleaned)
    return candidates


def extract_boundaries(lines: list[str]) -> tuple[list[str], list[str], bool]:
    """Return (allowed_paths, forbidden_paths, has_boundaries)."""
    items = extract_list_field(lines, "Boundaries")
    scalar = extract_scalar_field(lines, "Boundaries")
    has_boundaries = bool(items or scalar)
    if not items and scalar:
        items = [scalar]
    allowed: list[str] = []
    forbidden: list[str] = []
    for item in items:
        lower = item.lower()
        paths = _extract_paths_from_text(item)
        if not paths:
            continue
        if any(token in lower for token in ("must-not-touch", "forbidden", "do not", "not touch")):
            forbidden.extend(paths)
        elif "must-touch" in lower or "allowed" in lower:
            allowed.extend(paths)
        else:
            allowed.extend(paths)
    return _dedupe(allowed), _dedupe(forbidden), has_boundaries


def extract_section(lines: list[str], title: str) -> list[str]:
    """Return section body lines for a given heading (without the heading line)."""
    in_section = False
    collected: list[str] = []
    for line in lines:
        match = SECTION_HEADER_RE.match(line)
        if match:
            heading = match.group(1).strip()
            if in_section:
                break
            if heading == title:
                in_section = True
            continue
        if in_section:
            collected.append(line)
    return collected


def parse_test_execution(lines: list[str]) -> dict[str, object]:
    profile = (extract_scalar_field(lines, "profile") or "").strip()
    tasks_raw = extract_scalar_field(lines, "tasks") or ""
    filters_raw = extract_scalar_field(lines, "filters") or ""
    cwd = (extract_scalar_field(lines, "cwd") or "").strip()
    when = (extract_scalar_field(lines, "when") or "").strip()
    reason = (extract_scalar_field(lines, "reason") or "").strip()
    tasks_list = extract_list_field(lines, "tasks")
    filters_list = extract_list_field(lines, "filters")
    tasks: list[str] = []
    if tasks_list:
        for item in tasks_list:
            tasks.extend(_split_task_commands(item))
    elif tasks_raw:
        tasks = _split_task_commands(tasks_raw)
    filters: list[str] = []
    if filters_list:
        filters = filters_list
    elif filters_raw:
        filters = [item.strip() for item in re.split(r"\s*,\s*", filters_raw) if item.strip()]
    return {
        "profile": profile,
        "tasks": tasks,
        "filters": filters,
        "cwd": cwd,
        "when": when,
        "reason": reason,
    }
