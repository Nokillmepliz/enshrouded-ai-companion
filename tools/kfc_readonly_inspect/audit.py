"""Offline audit helpers for the Stage 10.5 KFC inspector.

This module performs no installation and never writes to the game directory.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tomllib
from typing import Callable


PINNED_KFC_REV = "16708594d686b030d909f2d835b199d879ea9ad8"
REQUIRED_RUST = (1, 88, 0)
REQUIRED_EDITION = "2024"
GAME_INPUTS = ("enshrouded.kfc", "enshrouded.kfc_resources", "enshrouded.exe")


class AuditError(ValueError):
    pass


def parse_rust_version(output: str) -> tuple[int, int, int]:
    match = re.search(r"\brustc\s+(\d+)\.(\d+)\.(\d+)\b", output)
    if not match:
        raise AuditError("rust_version_unrecognized")
    return tuple(map(int, match.groups()))


def rust_compatible(output: str) -> bool:
    return parse_rust_version(output) >= REQUIRED_RUST


def detect_toolchain(
    which: Callable[[str], str | None] = shutil.which,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict:
    found = {name: which(name) for name in ("rustc", "cargo", "cl", "link", "clang-cl")}
    versions: dict[str, str | None] = {"rustc": None, "cargo": None}
    for name in versions:
        if found[name]:
            result = run(
                [found[name], "--version"], capture_output=True, text=True,
                check=False, timeout=10,
            )
            versions[name] = result.stdout.strip() if result.returncode == 0 else None
    try:
        compatible = bool(versions["rustc"] and rust_compatible(versions["rustc"]))
    except AuditError:
        compatible = False
    native_compiler = found["cl"] or found["clang-cl"]
    return {
        "tools": found,
        "versions": versions,
        "rust_compatible": compatible,
        "native_compiler_available": bool(native_compiler),
        "msvc_linker_available": bool(found["link"]),
        "status": "READY" if compatible and native_compiler and found["cargo"] else "BLOCKED",
    }


def audit_manifest(path: str | Path) -> dict:
    manifest = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    package = manifest.get("package", {})
    dependencies = manifest.get("dependencies", {})
    kfc = dependencies.get("kfc")
    failures = []
    if package.get("edition") != REQUIRED_EDITION:
        failures.append("edition_not_2024")
    try:
        parts = list(map(int, str(package.get("rust-version", "")).split(".")))
        version = tuple((parts + [0, 0, 0])[:3])
    except ValueError:
        version = ()
    if version != REQUIRED_RUST:
        failures.append("rust_version_not_pinned")
    if not isinstance(kfc, dict):
        failures.append("kfc_dependency_missing")
    else:
        if kfc.get("rev") != PINNED_KFC_REV:
            failures.append("kfc_revision_not_pinned")
        if kfc.get("git") != "https://github.com/Brabb3l/kfc-parser.git":
            failures.append("kfc_source_unexpected")
        if kfc.get("features") != ["resource"]:
            failures.append("kfc_features_unexpected")
    if set(dependencies) != {"anyhow", "serde_json", "kfc"}:
        failures.append("direct_dependency_set_unexpected")
    return {
        "edition": package.get("edition"),
        "rust_version": package.get("rust-version"),
        "kfc_revision": kfc.get("rev") if isinstance(kfc, dict) else None,
        "direct_dependencies": sorted(dependencies),
        "cargo_lock_present": Path(path).with_name("Cargo.lock").is_file(),
        "failures": failures,
        "ok": not failures,
    }


def audit_source(path: str | Path) -> dict:
    source = Path(path).read_text(encoding="utf-8")
    forbidden = (
        "KFCWriter", "write_resource", "create_resource", "remove_dir_all",
        "set_resources", "PatchWriter",
    )
    found = [token for token in forbidden if token in source]
    required = (
        "KFCReader", "File::open", "create_new(true)",
        "refusing to write inside game directory", "refusing to overwrite output",
    )
    missing = [token for token in required if token not in source]
    return {"forbidden_tokens": found, "missing_guards": missing, "ok": not found and not missing}


def _within(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((os.path.normcase(path), os.path.normcase(root))) == os.path.normcase(root)
    except ValueError:
        return False


def canonical_plan(game_dir: str | Path, output: str | Path | None = None) -> dict:
    game = Path(game_dir).resolve(strict=True)
    if not game.is_dir():
        raise AuditError("game_directory_invalid")
    inputs = []
    for name in GAME_INPUTS:
        value = (game / name).resolve(strict=True)
        if not value.is_file():
            raise AuditError(f"required_input_missing:{name}")
        inputs.append(value)
    output_path = None
    if output is not None:
        raw = Path(output)
        if not raw.is_absolute():
            raw = Path.cwd() / raw
        parent = raw.parent.resolve(strict=True)
        output_path = parent / raw.name
        if any(os.path.normcase(output_path) == os.path.normcase(value) for value in inputs):
            raise AuditError("input_output_collision")
        if _within(output_path, game):
            raise AuditError("output_inside_game_forbidden")
        if output_path.exists():
            raise AuditError("output_exists")
    return {
        "game_dir": str(game),
        "inputs": [str(value) for value in inputs],
        "output": str(output_path) if output_path else "STDOUT",
    }


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def integrity_snapshot(paths: list[str | Path]) -> dict[str, str]:
    return {str(Path(path).resolve(strict=True)): sha256_file(path) for path in paths}


def deterministic_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def audit_upstream_lock(path: str | Path) -> dict:
    lock = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    packages = {item["name"]: item for item in lock.get("package", [])}
    required = ("anyhow", "serde_json", "zstd", "zstd-safe", "zstd-sys", "cc")
    missing = [name for name in required if name not in packages]
    versions = {name: packages[name]["version"] for name in required if name in packages}
    zstd_sys_deps = packages.get("zstd-sys", {}).get("dependencies", [])
    return {
        "lock_version": lock.get("version"),
        "versions": versions,
        "missing": missing,
        "zstd_sys_uses_cc": any(value.split()[0] == "cc" for value in zstd_sys_deps),
        "requires_native_c_compiler": True,
        "ok": lock.get("version") == 4 and not missing and any(
            value.split()[0] == "cc" for value in zstd_sys_deps
        ),
    }


def local_environment(project_root: str | Path) -> dict[str, str]:
    root = Path(project_root).resolve(strict=True)
    rustup = root / ".tools" / "rust"
    cargo = root / ".tools" / "cargo"
    target = root / ".tools" / "kfc-inspector" / "target"
    return {
        "RUSTUP_HOME": str(rustup),
        "CARGO_HOME": str(cargo),
        "CARGO_TARGET_DIR": str(target),
        "RUSTUP_INIT_SKIP_PATH_CHECK": "yes",
    }
