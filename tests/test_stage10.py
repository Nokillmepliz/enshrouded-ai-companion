import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from companion.stage10 import (
    EXPECTED_EML_DBGHELP_SHA256, EXPECTED_EMF_LOADER_SHA256, EXPECTED_GAME_SHA256,
    Stage10Error, audit_pe, create_backup, detect_game_process, eml_log_writer_finalized,
    evaluate_evidence, install,
    parse_evidence, preflight, rollback_added_files, sha256, validate_observer,
    verify_backup, restore_game_data,
)


ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "experimental" / "eml_humanoid"
OBSERVER = ROOT / "mods" / "aic_template_observer"


def evidence(**changes):
    value = {
        "format": "aic_eml_humanoid_evidence_v1",
        "patch_version": "0.1.0",
        "template_guid": "a1c90001-5e4d-4a91-8a1c-000000000001",
        "source_guid": "e3736dff-0ad2-47fc-903c-66c1775836e8",
        "npc_id": "2939921867", "faction": "PlayerAlly",
        "model_guid": "model-human", "source_model_guid": "model-human",
        "animation_graph_guid": "graph-human", "source_animation_graph_guid": "graph-human",
        "components": "A,B", "source_components": "A,B", "component_clone": "true",
        "source_unchanged": "true", "resource_lookup_after_create": "true",
        "source_registered": "true", "registry_added": "true",
    }
    value.update(changes)
    return value


class Stage10EvidenceTests(unittest.TestCase):
    def test_complete_evidence_still_requires_writer_finalization(self):
        self.assertFalse(evaluate_evidence(evidence(), writer_finalized=False)["ok"])
        self.assertTrue(evaluate_evidence(evidence(), writer_finalized=True)["ok"])

    def test_unknown_template_wrong_faction_npc_and_story_change_fail(self):
        cases = (
            {"template_guid": "unknown"}, {"faction": "Vukah"},
            {"npc_id": "1"}, {"source_unchanged": "false"},
        )
        for change in cases:
            with self.subTest(change=change):
                self.assertFalse(evaluate_evidence(evidence(**change), writer_finalized=True)["ok"])

    def test_incomplete_component_or_reflection_fingerprint_fails(self):
        self.assertFalse(evaluate_evidence(evidence(components=""), writer_finalized=True)["ok"])
        self.assertFalse(evaluate_evidence(evidence(model_guid="UNAVAILABLE"), writer_finalized=True)["ok"])
        self.assertFalse(evaluate_evidence(evidence(animation_graph_guid="UNAVAILABLE"), writer_finalized=True)["ok"])
        self.assertFalse(evaluate_evidence(evidence(source_model_guid="different"), writer_finalized=True)["ok"])
        self.assertFalse(evaluate_evidence(
            evidence(source_animation_graph_guid="different"), writer_finalized=True)["ok"])

    def test_evidence_parser_rejects_duplicates_and_bad_lines(self):
        with self.assertRaisesRegex(Stage10Error, "evidence_malformed"):
            parse_evidence("a=1\na=2\n")
        with self.assertRaisesRegex(Stage10Error, "evidence_malformed"):
            parse_evidence("not a field\n")

    def test_writer_finalization_needs_positive_ready_and_applied_signals(self):
        good = "AIC_EML_TEMPLATE_READY a1c90001-5e4d-4a91-8a1c-000000000001 2939921867\nApplied 2 patches"
        self.assertTrue(eml_log_writer_finalized(good))
        self.assertFalse(eml_log_writer_finalized("Applied 2 patches"))
        self.assertFalse(eml_log_writer_finalized(good.replace("Applied 2", "Applied 0")))


class Stage10ObserverTests(unittest.TestCase):
    def test_observer_is_disabled_and_read_only(self):
        self.assertIn("compare", validate_observer(OBSERVER))
        source = (OBSERVER / "main.lua").read_text(encoding="utf-8")
        for forbidden in ("emf.spawn", "emf.destroy", "emf.emit", "world:set", "on_tick", "os.remove"):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("'w'", source)
        self.assertIn("UNAVAILABLE_WITHOUT_ENTITY", source)

    def test_observer_lua_sources_compile(self):
        from lupa import LuaRuntime
        lua = LuaRuntime(unpack_returned_tuples=True)
        compile_lua = lua.eval("load")
        for name in ("main.lua", "json.lua"):
            result = compile_lua((OBSERVER / name).read_text(encoding="utf-8"), name)
            if isinstance(result, tuple):
                self.fail(result[1])
            self.assertTrue(callable(result))


class Stage10PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.game = self.root / "game"
        (self.game / "emf").mkdir(parents=True)
        for name in ("enshrouded.exe", "enshrouded.kfc", "enshrouded.kfc_resources", "dinput8.dll"):
            (self.game / name).write_bytes(name.encode())
        (self.game / "emf" / "emf_core.log").write_text("known build 1273043", encoding="utf-8")
        self.eml = self.root / "dbghelp.dll"
        self.eml.write_bytes(b"eml")

    def tearDown(self):
        self.temp.cleanup()

    def hashes(self, path):
        name = Path(path).name
        return {"enshrouded.exe": EXPECTED_GAME_SHA256, "dinput8.dll": EXPECTED_EMF_LOADER_SHA256,
                "dbghelp.dll": EXPECTED_EML_DBGHELP_SHA256}.get(name, "irrelevant")

    def run_preflight(self, **kwargs):
        with patch("companion.stage10.sha256", side_effect=self.hashes):
            return preflight(self.game, self.eml, PATCH, OBSERVER, expected_game_dir=self.game, **kwargs)

    def test_valid_dry_run(self):
        result = self.run_preflight()
        self.assertTrue(result["ok"])
        self.assertFalse(result["phase_b_allowed"])
        self.assertGreater(result["game_disk_free_bytes"], result["game_disk_required_bytes"])

    def test_process_detection_is_positive_and_fails_closed(self):
        completed = __import__("subprocess").CompletedProcess(
            [], 0, stdout='"enshrouded.exe","123","Console"', stderr="")
        with patch("companion.stage10.subprocess.run", return_value=completed):
            self.assertTrue(detect_game_process())
        failed = __import__("subprocess").CompletedProcess([], 1, stdout="", stderr="error")
        with patch("companion.stage10.subprocess.run", return_value=failed):
            with self.assertRaisesRegex(Stage10Error, "game_process_check_failed"):
                detect_game_process()

    def test_wrong_path_and_running_game_are_rejected(self):
        with self.assertRaisesRegex(Stage10Error, "unexpected_game_path"):
            with patch("companion.stage10.sha256", side_effect=self.hashes):
                preflight(self.game, self.eml, PATCH, OBSERVER, expected_game_dir=self.root / "other")
        with self.assertRaisesRegex(Stage10Error, "game_process_running"):
            self.run_preflight(game_running=True)

    def test_unknown_build_missing_eml_and_incompatible_loader_are_rejected(self):
        (self.game / "emf" / "emf_core.log").write_text("known build 999", encoding="utf-8")
        with self.assertRaisesRegex(Stage10Error, "build_marker_unconfirmed"):
            self.run_preflight()
        (self.game / "emf" / "emf_core.log").write_text("known build 1273043", encoding="utf-8")
        self.eml.unlink()
        with self.assertRaisesRegex(Stage10Error, "eml_binary_missing"):
            self.run_preflight()
        self.eml.write_bytes(b"eml")
        with patch("companion.stage10.sha256", return_value="wrong"):
            with self.assertRaisesRegex(Stage10Error, "unknown_game_build"):
                preflight(self.game, self.eml, PATCH, OBSERVER, expected_game_dir=self.game)

        def wrong_loader(path):
            if Path(path).name == "dinput8.dll":
                return "wrong"
            return self.hashes(path)

        with patch("companion.stage10.sha256", side_effect=wrong_loader):
            with self.assertRaisesRegex(Stage10Error, "incompatible_emf_loader"):
                preflight(self.game, self.eml, PATCH, OBSERVER, expected_game_dir=self.game)

    def test_conflicting_dll_and_repeated_install_are_rejected(self):
        (self.game / "dbghelp.dll").write_bytes(b"foreign")
        with self.assertRaisesRegex(Stage10Error, "conflicting_or_repeated"):
            self.run_preflight()
        (self.game / "dbghelp.dll").unlink()
        (self.game / "mods" / "aic_eml_humanoid").mkdir(parents=True)
        with self.assertRaisesRegex(Stage10Error, "patch_already_installed"):
            self.run_preflight()

    def test_stale_evidence_is_rejected(self):
        stale = self.game / "export" / "aic_eml_humanoid" / "template_evidence_v1.txt"
        stale.parent.mkdir(parents=True)
        stale.write_text("old", encoding="utf-8")
        with self.assertRaisesRegex(Stage10Error, "stale_evidence_present"):
            self.run_preflight()

    def test_eml_config_backup_mod_temp_observer_config_and_receipt_are_rejected(self):
        collisions = (
            (self.game / "eml.json", "conflicting_or_repeated_eml_config"),
            (self.game / "enshrouded.kfc.bak", "unexpected_kfc_backup"),
            (self.game / "mods" / "foreign" / "mod.json", "conflicting_eml_mods_present"),
            (self.game / "emf" / "config" / "aic_template_observer.ini",
             "observer_config_already_installed"),
            (self.game / "orphan.stage10-install", "partial_install_temporary_present"),
        )
        for path, error in collisions:
            with self.subTest(error=error):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("collision", encoding="utf-8")
                with self.assertRaisesRegex(Stage10Error, error):
                    self.run_preflight()
                path.unlink()
                for parent in (path.parent, path.parent.parent):
                    if parent not in (self.game, self.game / "emf") and parent.is_dir():
                        try:
                            parent.rmdir()
                        except OSError:
                            pass
        receipt = self.root / "install-receipt.json"
        receipt.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(Stage10Error, "partial_or_repeated_install_receipt"):
            self.run_preflight(receipt_path=receipt)


class Stage10BackupInstallRollbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.game, self.saves = self.root / "game", self.root / "saves"
        self.game.mkdir(); self.saves.mkdir()
        (self.game / "enshrouded.kfc").write_bytes(b"kfc")
        (self.game / "enshrouded.kfc_resources").write_bytes(b"resources")
        (self.saves / "character0.ksd").write_bytes(b"character")
        (self.saves / "world0.ksd").write_bytes(b"world")
        self.backup = self.root / "backup"
        self.manifest = Path(create_backup(
            self.game, self.saves, self.backup, apply=True, game_running=False)["manifest"])
        self.eml = self.root / "eml-source.dll"; self.eml.write_bytes(b"eml")
        self.receipt = self.root / "receipt.json"

    def verified_install(self, *args, **kwargs):
        real_sha256 = sha256

        def hashes(path):
            if Path(path).resolve() == self.eml.resolve():
                return EXPECTED_EML_DBGHELP_SHA256
            return real_sha256(path)

        with patch("companion.stage10.sha256", side_effect=hashes):
            return install(*args, **kwargs)

    def tearDown(self):
        self.temp.cleanup()

    def test_backup_plan_and_verified_copy(self):
        plan = create_backup(self.game, self.saves, self.root / "other", apply=False)
        self.assertEqual(plan["mode"], "dry_run")
        self.assertTrue(verify_backup(self.manifest))
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertTrue(all(entry.get("reason") for entry in data["entries"]))

    def test_backup_hash_mismatch_is_rejected(self):
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        Path(data["entries"][0]["backup"]).write_bytes(b"corrupt")
        self.assertFalse(verify_backup(self.manifest))
        with self.assertRaisesRegex(Stage10Error, "verified_backup_required"):
            install(self.game, self.eml, PATCH, OBSERVER, self.manifest, self.receipt, apply=False)

    def test_legacy_manifest_shape_is_rejected_without_exception(self):
        legacy = self.root / "legacy-manifest.json"
        legacy.write_text(json.dumps({
            "verified": True,
            "entries": {"local/character0.ksd": {"sha256": "old-format"}},
        }), encoding="utf-8")
        self.assertFalse(verify_backup(legacy))

    def test_install_is_dry_run_by_default(self):
        plan = self.verified_install(
            self.game, self.eml, PATCH, OBSERVER, self.manifest, self.receipt)
        self.assertEqual(plan["mode"], "dry_run")
        self.assertFalse((self.game / "dbghelp.dll").exists())

    def test_repeat_and_partial_install_are_fail_closed(self):
        with self.assertRaisesRegex(Stage10Error, "injected_partial_install"):
            self.verified_install(self.game, self.eml, PATCH, OBSERVER, self.manifest,
                                  self.receipt, apply=True, fail_after=5, game_running=False)
        self.assertEqual(json.loads(self.receipt.read_text())["state"], "in_progress")
        receipt = json.loads(self.receipt.read_text())
        self.assertRegex(receipt["run_token"], r"^[0-9a-f]{32}$")
        installed_patch = self.game / "mods" / "aic_eml_humanoid" / "src" / "mod.lua"
        self.assertIn(receipt["run_token"], installed_patch.read_text(encoding="utf-8"))
        self.assertNotIn("__AIC_STAGE10_RUN_TOKEN__", installed_patch.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(Stage10Error, "installation_collision"):
            self.verified_install(self.game, self.eml, PATCH, OBSERVER, self.manifest,
                                  self.root / "again.json", apply=True, game_running=False)

    def test_partial_install_can_rollback_only_unchanged_added_files(self):
        with self.assertRaises(Stage10Error):
            self.verified_install(self.game, self.eml, PATCH, OBSERVER, self.manifest,
                                  self.receipt, apply=True, fail_after=2, game_running=False)
        plan = rollback_added_files(self.game, self.receipt)
        self.assertEqual(plan["mode"], "dry_run")
        rollback_added_files(self.game, self.receipt, apply=True, game_running=False)
        self.assertFalse((self.game / "dbghelp.dll").exists())

    def test_rollback_refuses_unknown_changed_state(self):
        with self.assertRaises(Stage10Error):
            self.verified_install(self.game, self.eml, PATCH, OBSERVER, self.manifest,
                                  self.receipt, apply=True, fail_after=1, game_running=False)
        (self.game / "dbghelp.dll").write_bytes(b"foreign replacement")
        with self.assertRaisesRegex(Stage10Error, "rollback_state_unknown"):
            rollback_added_files(self.game, self.receipt, apply=True, game_running=False)

    def test_mutation_helpers_reject_running_game(self):
        with self.assertRaisesRegex(Stage10Error, "game_process_running"):
            self.verified_install(self.game, self.eml, PATCH, OBSERVER, self.manifest,
                                  self.receipt, apply=True, game_running=True)
        self.receipt.write_text(json.dumps({"applied": []}), encoding="utf-8")
        with self.assertRaisesRegex(Stage10Error, "game_process_running"):
            rollback_added_files(self.game, self.receipt, apply=True, game_running=True)
        with self.assertRaisesRegex(Stage10Error, "game_process_running"):
            restore_game_data(self.game, self.manifest, apply=True, game_running=True)

    def test_game_data_restore_refuses_unreviewed_outputs_and_verifies_restore(self):
        (self.game / "enshrouded.kfc").write_bytes(b"patched")
        (self.game / "enshrouded.kfc_resources").write_bytes(b"appended")
        (self.game / "enshrouded.kfc.bak").write_bytes(b"kfc")
        (self.game / "enshrouded_055.dat").write_bytes(b"new")
        with self.assertRaisesRegex(Stage10Error, "unknown_runtime_outputs"):
            restore_game_data(self.game, self.manifest)
        plan = restore_game_data(self.game, self.manifest, approved_new_dat=("enshrouded_055.dat",))
        self.assertEqual(plan["mode"], "dry_run")
        result = restore_game_data(
            self.game, self.manifest, approved_new_dat=("enshrouded_055.dat",), apply=True,
            game_running=False)
        self.assertEqual((self.game / "enshrouded.kfc").read_bytes(), b"kfc")
        self.assertEqual((self.game / "enshrouded.kfc_resources").read_bytes(), b"resources")
        self.assertFalse((self.game / "enshrouded_055.dat").exists())
        self.assertTrue(Path(result["report"]).is_file())


class Stage10BinaryAuditTests(unittest.TestCase):
    def test_downloaded_official_files_match_release_digests_when_present(self):
        downloads = ROOT / "runtime" / "stage10" / "downloads"
        if not downloads.exists():
            self.skipTest("local ignored audit artifacts are absent")
        self.assertEqual(sha256(downloads / "dbghelp.dll"), EXPECTED_EML_DBGHELP_SHA256)
        self.assertEqual(sha256(downloads / "emm.exe"),
                         "b1133f6b8ea7000596cc7710901bd8307b48165b0e650c0487a611d90ea49305")
        for name in ("dbghelp.dll", "emm.exe"):
            audit = audit_pe(downloads / name)
            self.assertEqual(audit["machine"], "0x8664")
            self.assertEqual(audit["magic"], "0x20b")


if __name__ == "__main__":
    unittest.main()
