"""Read-only parser for EMF's generated reflection header.

This parses source metadata only. It does not open Enshrouded or game assets.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


TYPE_RE = re.compile(
    r'^\s*\{"([^"]+)", "([^"]+)", 0x[0-9a-f]+u, '
    r'(\d+), (\d+), (\d+), (\d+)\},$'
)
FIELD_RE = re.compile(
    r'^\s*\{"([^"]+)", (\d+), (\d+), Kind::(\w+), '
    r'0x([0-9a-f]+), (\d+)\},$'
)


def _array_lines(text: str, declaration: str) -> list[str]:
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if declaration in line) + 1
        end = next(i for i in range(start, len(lines)) if lines[i].strip() == "};")
    except StopIteration as exc:
        raise ValueError(f"reflection_array_missing:{declaration}") from exc
    return lines[start:end]


def parse_reflection(path: str | Path) -> dict[str, dict]:
    text = Path(path).read_text(encoding="utf-8")
    types = []
    for line in _array_lines(text, "Type kTypes"):
        match = TYPE_RE.match(line)
        if match:
            name, short_name, size, first, count, component = match.groups()
            types.append({
                "name": name, "short_name": short_name, "size": int(size),
                "first_field": int(first), "field_count": int(count),
                "template_component": bool(int(component)),
            })
    fields = []
    for line in _array_lines(text, "Field kFields"):
        match = FIELD_RE.match(line)
        if match:
            name, offset, size, kind, nested, count = match.groups()
            fields.append({
                "name": name, "offset": int(offset), "size": int(size),
                "kind": kind, "nested_index": int(nested, 16), "count": int(count),
            })
    if not types or not fields:
        raise ValueError("reflection_arrays_not_parsed")
    by_index = {index: value["name"] for index, value in enumerate(types)}
    result = {}
    for value in types:
        first, count = value["first_field"], value["field_count"]
        rendered = []
        for field in fields[first:first + count]:
            item = {key: field[key] for key in ("name", "offset", "size", "kind", "count")}
            if field["kind"] == "Struct" and field["nested_index"] != 0xFFFF:
                item["nested_type"] = by_index.get(field["nested_index"], "UNKNOWN_TYPE_INDEX")
            rendered.append(item)
        result[value["name"]] = {
            "size": value["size"],
            "template_component": value["template_component"],
            "fields": rendered,
        }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("header", type=Path)
    parser.add_argument("types", nargs="+")
    args = parser.parse_args(argv)
    schema = parse_reflection(args.header)
    output = {name: schema.get(name, {"status": "NOT_FOUND"}) for name in args.types}
    print(json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
