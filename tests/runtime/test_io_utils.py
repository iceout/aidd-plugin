from __future__ import annotations

import json
from pathlib import Path

from aidd_runtime import io_utils


def test_utc_timestamp_uses_utc_suffix() -> None:
    value = io_utils.utc_timestamp()
    assert value.endswith("Z")
    assert "T" in value


def test_parse_front_matter_from_text_and_lines() -> None:
    text = """---\ntitle: Demo\nowner: aidd\n---\nbody\n"""
    parsed = io_utils.parse_front_matter(text)
    assert parsed == {"title": "Demo", "owner": "aidd"}

    lines = ["---", "a: 1", "bad-line", "b: two", "---", "tail"]
    parsed_lines = io_utils.parse_front_matter(lines)
    assert parsed_lines == {"a": "1", "b": "two"}

    assert io_utils.parse_front_matter("no-front-matter") == {}


def test_dump_yaml_handles_dict_list_scalar() -> None:
    payload = {
        "name": "demo",
        "meta": {"enabled": True},
        "items": ["a", {"k": 1}],
    }
    lines = io_utils.dump_yaml(payload)
    rendered = "\n".join(lines)
    assert 'name: "demo"' in rendered
    assert "meta:" in rendered
    assert "items:" in rendered
    assert '- "a"' in rendered

    scalar_lines = io_utils.dump_yaml(123)
    assert scalar_lines == ["123"]


def test_read_write_append_jsonl_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "logs" / "events.jsonl"
    records = [{"k": "v"}, {"n": 1}]

    io_utils.write_jsonl(path, records)
    loaded = io_utils.read_jsonl(path)
    assert loaded == records

    io_utils.append_jsonl(path, {"tail": True})
    loaded2 = io_utils.read_jsonl(path)
    assert loaded2[-1] == {"tail": True}


def test_read_jsonl_skips_invalid_lines_and_handles_oserror(tmp_path: Path) -> None:
    path = tmp_path / "mixed.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"ok": 1}',
                "not-json",
                '["array-is-ignored"]',
                '{"ok": 2}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert io_utils.read_jsonl(path) == [{"ok": 1}, {"ok": 2}]

    # Path exists but cannot be opened as a file.
    directory_path = tmp_path / "as-dir"
    directory_path.mkdir()
    assert io_utils.read_jsonl(directory_path) == []


def test_write_jsonl_uses_utf8_and_atomic_replace(tmp_path: Path) -> None:
    path = tmp_path / "out" / "unicode.jsonl"
    io_utils.write_jsonl(path, [{"text": "你好"}])

    content = path.read_text(encoding="utf-8").strip()
    assert json.loads(content) == {"text": "你好"}
    assert not (path.with_suffix(path.suffix + ".tmp")).exists()
