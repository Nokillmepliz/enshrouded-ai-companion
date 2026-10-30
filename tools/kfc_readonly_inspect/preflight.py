"""Read-only safety preflight for the Rust KFC inspector source."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import struct


class InspectorPreflightError(ValueError):
    pass


def inspect_plan(game_dir: str | Path, output: str | Path | None = None) -> dict:
    game = Path(game_dir).resolve()
    kfc = game / "enshrouded.kfc"
    resources = game / "enshrouded.kfc_resources"
    executable = game / "enshrouded.exe"
    for path in (kfc, resources, executable):
        if not path.is_file():
            raise InspectorPreflightError(f"required_input_missing:{path.name}")
    with kfc.open("rb") as stream:
        header = stream.read(12)
    if len(header) != 12:
        raise InspectorPreflightError("kfc_header_truncated")
    magic, declared_size, marker = struct.unpack("<III", header)
    if magic != 0x3443464B:
        raise InspectorPreflightError("kfc_magic_invalid")
    if marker != 12 or declared_size < 12 or declared_size > kfc.stat().st_size:
        raise InspectorPreflightError("kfc_header_invalid")
    output_path = None
    if output is not None:
        output_path = Path(output).resolve()
        if output_path == game or game in output_path.parents:
            raise InspectorPreflightError("output_inside_game_forbidden")
        if output_path.exists():
            raise InspectorPreflightError("output_exists")
        if not output_path.parent.is_dir():
            raise InspectorPreflightError("output_parent_missing")
    cargo, rustc = shutil.which("cargo"), shutil.which("rustc")
    return {
        "mode": "READ_ONLY_PREFLIGHT",
        "kfc_header": "KFC4",
        "inputs": [str(kfc), str(resources), str(executable)],
        "output": str(output_path) if output_path else "STDOUT",
        "cargo": cargo,
        "rustc": rustc,
        "status": "READY_TO_BUILD" if cargo and rustc else "BLOCKED_TOOLCHAIN",
        "writes_performed": False,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("game_dir")
    parser.add_argument("--output")
    args = parser.parse_args()
    print(json.dumps(inspect_plan(args.game_dir, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
