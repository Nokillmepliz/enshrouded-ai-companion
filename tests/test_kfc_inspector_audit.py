import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.kfc_readonly_inspect.audit import (
    AuditError,
    audit_manifest,
    audit_source,
    audit_upstream_lock,
    canonical_plan,
    detect_toolchain,
    deterministic_json,
    integrity_snapshot,
    local_environment,
    parse_rust_version,
    rust_compatible,
)
from tools.kfc_readonly_inspect.preflight import InspectorPreflightError, inspect_plan


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "kfc_readonly_inspect"


def game_fixture(root: Path, *, header: bytes | None = None) -> Path:
    game = root / "game"
    game.mkdir()
    (game / "enshrouded.exe").write_bytes(b"fixture-exe")
    (game / "enshrouded.kfc_resources").write_bytes(b"fixture-resources")
    (game / "enshrouded.kfc").write_bytes(
        header if header is not None else b"KFC4" + (12).to_bytes(4, "little") + (12).to_bytes(4, "little")
    )
    return game


class ToolchainAuditTests(unittest.TestCase):
    def test_version_compatibility_is_explicit(self):
        self.assertEqual(parse_rust_version("rustc 1.88.0 (abc 2025-06-23)"), (1, 88, 0))
        self.assertTrue(rust_compatible("rustc 1.88.0 (abc)"))
        self.assertFalse(rust_compatible("rustc 1.87.0 (abc)"))
        with self.assertRaisesRegex(AuditError, "rust_version_unrecognized"):
            parse_rust_version("not-rust")

    def test_toolchain_detection_handles_absence_and_bad_version(self):
        self.assertEqual(detect_toolchain(which=lambda _: None)["status"], "BLOCKED")

        def which(name):
            return f"C:/{name}.exe"

        def run(command, **_):
            output = "broken" if command[0].endswith("rustc.exe") else "cargo 1.88.0"
            return subprocess.CompletedProcess(command, 0, output, "")

        self.assertEqual(detect_toolchain(which=which, run=run)["status"], "BLOCKED")

    def test_local_environment_is_project_scoped(self):
        env = local_environment(ROOT)
        for key in ("RUSTUP_HOME", "CARGO_HOME", "CARGO_TARGET_DIR"):
            self.assertTrue(Path(env[key]).is_relative_to(ROOT))
        self.assertEqual(env["RUSTUP_INIT_SKIP_PATH_CHECK"], "yes")
        self.assertNotIn("PATH", env)

    def test_manifest_and_source_are_pinned_read_only(self):
        manifest = audit_manifest(TOOL / "Cargo.toml")
        source = audit_source(TOOL / "src/main.rs")
        self.assertTrue(manifest["ok"], manifest)
        self.assertFalse(manifest["cargo_lock_present"])
        self.assertTrue(source["ok"], source)

    def test_pinned_upstream_lock_records_native_zstd_build(self):
        packages = ("anyhow", "serde_json", "zstd", "zstd-safe", "cc")
        content = "version = 4\n"
        for name in packages:
            content += f'[[package]]\nname = "{name}"\nversion = "1.0.0"\n'
        content += ('[[package]]\nname = "zstd-sys"\nversion = "2.0.15"\n'
                    'dependencies = ["cc"]\n')
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "Cargo.lock"
            lock.write_text(content, encoding="utf-8")
            result = audit_upstream_lock(lock)
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["lock_version"], 4)
            self.assertTrue(result["zstd_sys_uses_cc"])
            self.assertTrue(result["requires_native_c_compiler"])


class PathAndIntegrityTests(unittest.TestCase):
    def test_output_outside_game_is_canonicalized(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = game_fixture(root)
            report = root / "reports" / "report.json"
            report.parent.mkdir()
            plan = canonical_plan(game, report.parent / ".." / "reports" / "report.json")
            self.assertEqual(Path(plan["output"]), report)

    def test_output_inside_game_and_input_collision_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = game_fixture(Path(tmp))
            with self.assertRaisesRegex(AuditError, "output_inside_game_forbidden"):
                canonical_plan(game, game / "report.json")
            with self.assertRaisesRegex(AuditError, "input_output_collision"):
                canonical_plan(game, game / "enshrouded.kfc")

    def test_existing_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = game_fixture(root)
            output = root / "existing.json"
            output.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(AuditError, "output_exists"):
                canonical_plan(game, output)
            self.assertEqual(output.read_text(encoding="utf-8"), "keep")

    def test_directory_symlink_into_game_is_rejected_when_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = game_fixture(root)
            link = root / "game-link"
            try:
                os.symlink(game, link, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"directory symlink unavailable: {exc}")
            with self.assertRaisesRegex(AuditError, "output_inside_game_forbidden"):
                canonical_plan(game, link / "report.json")

    def test_hash_snapshot_detects_changes_and_json_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            value = Path(tmp) / "value.bin"
            value.write_bytes(b"before")
            before = integrity_snapshot([value])
            value.write_bytes(b"after")
            after = integrity_snapshot([value])
            self.assertNotEqual(before, after)
        self.assertEqual(
            deterministic_json({"b": 2, "a": 1}),
            deterministic_json({"a": 1, "b": 2}),
        )

    def test_invalid_and_unsupported_kfc_are_rejected_without_output(self):
        for header, reason in ((b"short", "kfc_header_truncated"),
                               (b"KFC3" + b"\x0c\x00\x00\x00" * 2, "kfc_magic_invalid")):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                game = game_fixture(root, header=header)
                output = root / "report.json"
                with self.assertRaisesRegex(InspectorPreflightError, reason):
                    inspect_plan(game, output)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
