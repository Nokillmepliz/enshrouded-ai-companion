"""SHA-256 integrity snapshots for the read-only Stage 10.5 inspection."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from tools.kfc_readonly_inspect.audit import sha256_file


def collect_inputs(game: Path, save_roots: list[Path]) -> list[tuple[str, Path]]:
    game = game.resolve(strict=True)
    selected = {
        game / "enshrouded.exe", game / "enshrouded.kfc",
        game / "enshrouded.kfc_resources", *game.glob("enshrouded_*.dat"),
        *game.glob("*.dll"),
    }
    files = [("game", path) for path in selected if path.is_file()]
    for index, root in enumerate(save_roots):
        root = root.resolve(strict=True)
        files.extend((f"saves_{index}", path) for path in root.rglob("*") if path.is_file())
    return sorted(files, key=lambda item: (item[0], str(item[1]).casefold()))


def snapshot(game: Path, save_roots: list[Path]) -> dict:
    records = []
    for group, path in collect_inputs(game, save_roots):
        stat = path.stat()
        records.append({
            "group": group,
            "path": str(path),
            "size": stat.st_size,
            "sha256": sha256_file(path),
        })
    return {
        "format": "aic_stage10_5_integrity_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "files": records,
    }


def compare(before: dict, after: dict) -> dict:
    def keyed(value: dict) -> dict[str, tuple[int, str]]:
        return {item["path"]: (item["size"], item["sha256"]) for item in value["files"]}
    left, right = keyed(before), keyed(after)
    return {
        "added": sorted(right.keys() - left.keys()),
        "removed": sorted(left.keys() - right.keys()),
        "changed": sorted(path for path in left.keys() & right.keys() if left[path] != right[path]),
        "identical": left == right,
    }


def write_new(path: Path, value: dict) -> None:
    path.parent.resolve(strict=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--save-root", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    value = snapshot(args.game, args.save_root)
    write_new(args.output, value)
    if args.compare:
        baseline = json.loads(args.compare.read_text(encoding="utf-8"))
        result = compare(baseline, value)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["identical"] else 3
    print(json.dumps({"files": len(value["files"]), "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
