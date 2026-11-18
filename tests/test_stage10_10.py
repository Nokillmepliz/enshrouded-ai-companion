"""Offline migration cases: no real game, saves, pipe or installer is used."""
import copy
from contextlib import contextmanager
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from companion import compatibility as c
from companion.stage10 import Stage10Error, rollback_added_files, restore_game_data, sha256
from tests import test_stage10 as historical_tests
from tests.test_stage10 import PATCH, OBSERVER


@contextmanager
def fixture():
    f = historical_tests.Stage10BackupInstallRollbackTests()
    f.setUp()
    try:
        yield f
    finally:
        f.tearDown()
        f.doCleanups()


def add_case(cls, name, callback):
    def test(self):
        callback(self)
    test.__name__ = "test_" + name
    setattr(cls, test.__name__, test)


class BuildAndProfileTests(unittest.TestCase):
    def test_known_historical_build(self):
        p = c.load_profile(1273043)
        self.assertEqual(c.detect_build(p["exe_sha256"], [p])["game_build"], 1273043)

    def test_known_new_build_remains_candidate(self):
        p = c.load_profile(1287369)
        self.assertEqual(c.detect_build(p["exe_sha256"], [p], metadata_build=1287369,
                                      steam_build="26430625"), p)
        self.assertFalse(p["installation_ready"])

    def test_missing_executable(self):
        with self.assertRaisesRegex(c.CompatibilityError, "GAME_EXECUTABLE_MISSING"):
            c.detect_build(None, [])

    def test_unknown_executable_hash(self):
        with self.assertRaisesRegex(c.CompatibilityError, "UNSUPPORTED_GAME_BUILD"):
            c.detect_build("0" * 64, [c.load_profile(1287369)])

    def test_metadata_mismatch(self):
        p = c.load_profile(1287369)
        with self.assertRaisesRegex(c.CompatibilityError, "BUILD_METADATA_MISMATCH"):
            c.detect_build(p["exe_sha256"], [p], metadata_build=1273043)

    def test_steam_id_is_not_internal_build(self):
        p = c.load_profile(1287369)
        with self.assertRaisesRegex(c.CompatibilityError, "STEAM_BUILD_ID_MISMATCH"):
            c.detect_build(p["exe_sha256"], [p], steam_build="1287369")

    def test_duplicate_hash_ambiguous(self):
        p = c.load_profile(1287369)
        with self.assertRaisesRegex(c.CompatibilityError, "UNSUPPORTED_GAME_BUILD"):
            c.detect_build(p["exe_sha256"], [p, p])

    def test_no_automatic_profile_fallback(self):
        with self.assertRaisesRegex(c.CompatibilityError, "UNSUPPORTED_GAME_BUILD"):
            c.load_profile(1287370)

    def test_profile_missing(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(c.CompatibilityError, "PROFILE_MISSING"):
                c.load_profile(1287369, Path(td))

    def test_profile_tampering(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "index.json").write_text(json.dumps({"1287369": "a" * 64}))
            (root / "1287369.json").write_text("{}")
            with self.assertRaisesRegex(c.CompatibilityError, "PROFILE_HASH_MISMATCH"):
                c.load_profile(1287369, root)

    def test_profile_identity_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            raw = json.dumps({"game_build": 1273043, "exe_sha256": "a" * 64}).encode()
            (root / "1287369.json").write_bytes(raw)
            (root / "index.json").write_text(json.dumps({"1287369": c.digest_bytes(raw)}))
            with self.assertRaisesRegex(c.CompatibilityError, "PROFILE_IDENTITY_MISMATCH"):
                c.load_profile(1287369, root)

    def test_historical_profile_is_readable_not_new_baseline(self):
        p = c.load_profile(1273043)
        self.assertEqual(p["expected_resource_metadata"]["component_count"], 81)
        self.assertEqual(p["status"], "HISTORICAL_ONLY")


class InventoryTests(unittest.TestCase):
    pass


for name, now, prior, kwargs, status in (
    ("changed_kfc", "new", "old", {}, "MODIFIED_UNKNOWN"),
    ("changed_resources", "new", "old", {"official": "other"}, "MODIFIED_UNKNOWN"),
    ("new_dat_unattributed", "new", None, {}, "NEW"),
    ("old_dat_number_reused", "new", "old", {"artifact": "old", "official": "new"}, "UPDATED_BY_GAME"),
    ("stale_mod_exact_hash", "old", "old", {"artifact": "old"}, "PREVIOUS_MOD_ARTIFACT"),
    ("modified_mod_cannot_delete", "new", "old", {"artifact": "old"}, "MODIFIED_UNKNOWN"),
    ("missing_mod", None, "old", {"artifact": "old"}, "MISSING"),
    ("incorrect_artifact_attribution", "new", None, {"artifact": "old"}, "MODIFIED_UNKNOWN"),
    ("unchanged_original_dat", "old", "old", {}, "UNCHANGED"),
):
    add_case(InventoryTests, name, lambda self, n=now, p=prior, k=kwargs, s=status:
             self.assertEqual(c.classify_file(n, p, **k), s))


class RollbackTests(unittest.TestCase):
    def installed(self, f):
        f.verified_install(f.game, f.eml, PATCH, OBSERVER, f.manifest, f.receipt,
                           apply=True, game_running=False)

    def test_correct_build_dry_run_preserves_all_files(self):
        with fixture() as f:
            self.installed(f)
            before = {p.relative_to(f.game).as_posix(): sha256(p) for p in f.game.rglob("*") if p.is_file()}
            self.assertEqual(len(rollback_added_files(f.game, f.receipt)["removable"]), 9)
            self.assertEqual(before, {p.relative_to(f.game).as_posix(): sha256(p) for p in f.game.rglob("*") if p.is_file()})

    def test_cross_build_apply_has_zero_deletions(self):
        with fixture() as f:
            self.installed(f)
            (f.game / "enshrouded.exe").write_bytes(b"new game")
            with self.assertRaisesRegex(Stage10Error, "ROLLBACK_BLOCKED_BUILD_MISMATCH"):
                rollback_added_files(f.game, f.receipt, apply=True, game_running=False)
            self.assertTrue((f.game / "dbghelp.dll").exists())

    def test_old_kfc_restore_rejected_before_copy(self):
        with fixture() as f:
            (f.game / "enshrouded.exe").write_bytes(b"new game")
            with self.assertRaisesRegex(Stage10Error, "ROLLBACK_BLOCKED_BUILD_MISMATCH"):
                restore_game_data(f.game, f.manifest, apply=True, game_running=False)
            self.assertEqual((f.game / "enshrouded.kfc").read_bytes(), b"kfc")

    def test_legacy_receipt_cannot_authorize_deletion(self):
        with fixture() as f:
            f.receipt.write_text(json.dumps({"game_build": 1273043, "applied": []}))
            with self.assertRaisesRegex(Stage10Error, "ROLLBACK_BLOCKED_UNKNOWN_ARTIFACT"):
                rollback_added_files(f.game, f.receipt)

    def test_changed_target_rejects_entire_plan(self):
        with fixture() as f:
            self.installed(f)
            (f.game / "eml.json").write_bytes(b"changed")
            with self.assertRaisesRegex(Stage10Error, "ROLLBACK_BLOCKED_FILE_MISMATCH"):
                rollback_added_files(f.game, f.receipt, apply=True, game_running=False)
            self.assertTrue((f.game / "dbghelp.dll").exists())

    def test_invalid_manifest_digest(self):
        with fixture() as f:
            self.installed(f)
            f.manifest.write_text(f.manifest.read_text() + " ")
            with self.assertRaisesRegex(Stage10Error, "ROLLBACK_BLOCKED_UNKNOWN_ARTIFACT"):
                rollback_added_files(f.game, f.receipt)

    def test_stale_baseline_identity(self):
        with fixture() as f:
            self.installed(f)
            data = json.loads(f.receipt.read_text()); data["baseline_identity"] = "0" * 64
            f.receipt.write_text(json.dumps(data))
            with self.assertRaisesRegex(Stage10Error, "stale_baseline"):
                rollback_added_files(f.game, f.receipt)

    def test_unknown_owned_path(self):
        with fixture() as f:
            self.installed(f)
            data = json.loads(f.receipt.read_text()); data["applied"].append({"path": "enshrouded.exe", "sha256": sha256(f.game / "enshrouded.exe")})
            f.receipt.write_text(json.dumps(data))
            with self.assertRaisesRegex(Stage10Error, "UNKNOWN_ARTIFACT:unowned_path"):
                rollback_added_files(f.game, f.receipt)

    def test_duplicate_receipt_path(self):
        with fixture() as f:
            self.installed(f)
            data = json.loads(f.receipt.read_text()); data["applied"].append(data["applied"][0])
            f.receipt.write_text(json.dumps(data))
            with self.assertRaisesRegex(Stage10Error, "duplicate_path"):
                rollback_added_files(f.game, f.receipt)

    def test_same_build_restore_requires_target_review(self):
        with fixture() as f:
            with self.assertRaisesRegex(Stage10Error, "review_required"):
                restore_game_data(f.game, f.manifest)

    def test_reused_dat_not_removed_by_number(self):
        with fixture() as f:
            (f.game / "enshrouded_055.dat").write_bytes(b"new official game payload")
            with self.assertRaisesRegex(Stage10Error, "review_required"):
                restore_game_data(f.game, f.manifest, approved_new_dat=("enshrouded_055.dat",), apply=True, game_running=False)
            self.assertEqual((f.game / "enshrouded_055.dat").read_bytes(), b"new official game payload")

    def test_historical_directory_cleanup_is_retired(self):
        from scripts.stage10_7_phase_b import clean_attributed_dirs
        with self.assertRaisesRegex(RuntimeError, "directory_hash_manifest_required"):
            clean_attributed_dirs({"known_runtime_outputs": [".cache", "logs", "export"]})


for path in ("../outside", "enshrouded.kfc:stream", "C:/other", "/absolute", "mods/../save", "mods\\escape"):
    add_case(RollbackTests, "unsafe_path_" + str(len(RollbackTests.__dict__)),
             lambda self, p=path: self.assertRaises(c.CompatibilityError, c.safe_target, Path.cwd(), p))


class ContractTests(unittest.TestCase):
    profile = {"emf_version": "0.6.18", "eml_version": "0.2.0", "lua_api": 46,
               "native_api": 46, "bridge_protocol": 1, "schema": "KFC4", "required_api": ["command", "reply"]}
    good = {**profile, "compatibility": "SUPPORTED", "available_api": ["command", "reply"]}

    def test_supported_contract(self):
        self.assertEqual(c.check_runtime_contract(self.profile, self.good), [])


for name, value in (("emf_version", "0.3.2"), ("eml_version", "0.3.2"), ("lua_api", 20),
                    ("native_api", 20), ("schema", "unknown"), ("compatibility", "UNKNOWN"),
                    ("available_api", ["command"]), ("experimental", True)):
    add_case(ContractTests, name, lambda self, n=name, v=value:
             self.assertTrue(c.check_runtime_contract(self.profile, {**self.good, n: v})))


class TemplateTests(unittest.TestCase):
    expected = {"source_guid": "source", "component_count": 82, "component_fingerprint": "new",
                "animation_graph": "graph"}
    good = {**expected, "custom_guid_collision": False, "npc_id_collision": False,
            "visual_references_valid": True, "dependencies_valid": True, "source_integrity": True}

    def test_new_source_not_forced_to_81(self):
        self.assertEqual(c.validate_template(self.expected, self.good), [])


for name, key, value in (("source_missing", "source_guid", None), ("source_changed", "source_guid", "other"),
    ("custom_collision", "custom_guid_collision", True), ("npc_collision", "npc_id_collision", True),
    ("old_count", "component_count", 81), ("old_fingerprint", "component_fingerprint", "412d61b0"),
    ("animation_changed", "animation_graph", "other"), ("visual_missing", "visual_references_valid", False),
    ("dependency_invalid", "dependencies_valid", False), ("source_modified", "source_integrity", False)):
    add_case(TemplateTests, name, lambda self, k=key, v=value:
             self.assertTrue(c.validate_template(self.expected, {**self.good, k: v})))


class HashKeyTests(unittest.TestCase):
    good = {"hair": {"type": "HashKey32", "reflection": "MappedStructValue.value", "value": 100818570}}

    def test_typed_known_value(self):
        self.assertEqual(c.validate_hashkeys(self.good, self.good, {"hair": 100818570}), [])

    def test_missing_field(self):
        self.assertTrue(c.validate_hashkeys({}, self.good, {"hair": 100818570}))

    def test_source_clone_mismatch(self):
        clone = copy.deepcopy(self.good); clone["hair"]["value"] = 7
        self.assertTrue(c.validate_hashkeys(self.good, clone, {"hair": 100818570}))

    def test_changed_source_requires_new_profile(self):
        self.assertTrue(c.validate_hashkeys(self.good, self.good, {"hair": 7}))

    def test_new_profile_allows_new_equal_values(self):
        data = copy.deepcopy(self.good); data["hair"]["value"] = 7
        self.assertEqual(c.validate_hashkeys(data, data, {"hair": 7}), [])


for name, key, value in (("primitive_representation", "type", "number"), ("reflection_unknown", "reflection", "guess"),
    ("negative", "value", -1), ("overflow", "value", 2**32), ("boolean_not_uint32", "value", True),
    ("float_not_uint32", "value", 1.0), ("string_not_uint32", "value", "100818570")):
    def check(self, key=key, value=value):
        bad = copy.deepcopy(self.good); bad["hair"][key] = value
        self.assertTrue(c.validate_hashkeys(bad, bad, {"hair": 100818570}))
    add_case(HashKeyTests, name, check)


class BridgeCaptureTests(unittest.TestCase):
    profile = {"bridge_protocol": 1, "game_build": 1287369}
    good = {"protocol": 1, "game_build": 1287369, "response_version": 1, "session": "fixture-session",
            "run_token": "fixture-token", "read_only": True, "spawn_forbidden": True}

    def check(self, cmd, data):
        return c.validate_observer_capture(cmd, data, profile=self.profile,
                                          run_token="fixture-token", session="fixture-session")


for cmd in ("status", "inspect", "compare"):
    add_case(BridgeCaptureTests, cmd, lambda self, cmd=cmd:
             self.assertEqual(self.check(cmd, {**self.good, "command": cmd}), []))
for cmd in ("spawn", "dismiss", "console", "load_world"):
    add_case(BridgeCaptureTests, "reject_" + cmd, lambda self, cmd=cmd:
             self.assertIn("mutation_command_rejected", self.check(cmd, self.good)))
for key, value in (("protocol", 2), ("session", "next"), ("game_build", 1273043), ("response_version", 2),
                   ("run_token", "stale"), ("read_only", 1), ("spawn_forbidden", False)):
    add_case(BridgeCaptureTests, "reject_" + key, lambda self, k=key, v=value:
             self.assertTrue(self.check("status", {**self.good, "command": "status", k: v})))


class EvidenceAndSchemaTests(unittest.TestCase):
    def test_unknown_evidence_is_valid_but_never_ready(self):
        doc = c.make_evidence({"game_build": 1287369}, {})
        self.assertEqual(c.validate_evidence(doc), [])
        self.assertFalse(doc["spawn_ready"])
        self.assertFalse(doc["installation_ready"])

    def test_missing_section(self):
        doc = c.make_evidence({}, {}); del doc["sections"]["ECS_DIFF"]
        self.assertIn("sections", c.validate_evidence(doc))

    def test_unproven_pass(self):
        doc = c.make_evidence({}, {}); doc["sections"]["ECS_DIFF"]["status"] = "PASS"
        self.assertIn("ECS_DIFF:unsupported_pass", c.validate_evidence(doc))

    def test_missing_provenance_field(self):
        doc = c.make_evidence({}, {}); del doc["sections"]["ECS_DIFF"]["provenance"]
        self.assertTrue(c.validate_evidence(doc))

    def test_offline_has_no_effect_imports(self):
        import ast
        tree = ast.parse(Path(c.__file__).read_text())
        imports = [x.module for x in ast.walk(tree) if isinstance(x, ast.ImportFrom)]
        imports += [a.name for x in ast.walk(tree) if isinstance(x, ast.Import) for a in x.names]
        self.assertFalse(set(imports) & {"subprocess", "socket", "ctypes", "companion.client", "os"})

    def test_previous_spawn_controller_remains_blocked(self):
        from companion.safe_spawn import offline_research_verdict
        self.assertFalse(offline_research_verdict()["spawn_ready"])


for key, value in (("installation_ready", True), ("spawn_ready", True), ("runtime_status", "LOAD_ONLY_SUCCESS"),
                   ("RUNTIME_RENDER_CONFIRMED", "CONFIRMED"), ("phase", "B")):
    def check(self, key=key, value=value):
        doc = c.make_evidence({}, {}); doc[key] = value
        self.assertIn(key, c.validate_evidence(doc))
    add_case(EvidenceAndSchemaTests, "reject_" + key, check)

for name, old, new, expected in (
    ("identical", {"hash": "a", "size": 4, "fields": []}, {"hash": "a", "size": 4, "fields": []}, "IDENTICAL"),
    ("offset_changed", {"hash": "a", "size": 4, "fields": [0]}, {"hash": "a", "size": 4, "fields": [1]}, "FIELDS_CHANGED"),
    ("layout_changed", {"hash": "a", "size": 4, "fields": []}, {"hash": "a", "size": 8, "fields": []}, "LAYOUT_CHANGED"),
    ("hash_changed", {"hash": "a", "size": 4, "fields": []}, {"hash": "b", "size": 4, "fields": []}, "TYPE_ID_CHANGED"),
    ("added", None, {"hash": "a"}, "ADDED"), ("removed", {"hash": "a"}, None, "REMOVED"),
    ("metadata_absent", {}, {}, "UNKNOWN"),
):
    add_case(EvidenceAndSchemaTests, "schema_" + name, lambda self, o=old, n=new, e=expected:
             self.assertEqual(c.compare_schema(o, n), e))


class LuaPreparationTests(unittest.TestCase):
    def rig(self):
        from lupa import LuaRuntime
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.globals().guard = lua.execute((Path(__file__).parents[1] /
            "experimental/eml_humanoid_next/compatibility_guard.lua").read_text())
        lua.execute('''
          setup={gender="Male",useNewProportions=false}
          profile={clean_baseline_verified=true,game_build=1287369,clone_guid="clone",source_guid="source",
             component_count=3,gender="Male",use_new_proportions=false,hashkeys={},animation_graph="graph",
             dependencies={{guid="dep",type="keen::RenderModel"}},npc_id=99}
          for _, key in ipairs({"voicePackId","presetId","hair","beard","hairColorId","beardColorId",
                                "skinColor","eyeBrowColor","eyeColor"}) do
            setup[key]={value=7}; profile.hashkeys[key]=7
          end
          source={data={components={
            {type="keen::ecs::CharacterSetup",value=setup},
            {type="keen::ecs::AnimationGraphResourceComponent2",value={animationGraph="graph"}},
            {type="keen::ecs::ActiveNpcState",value={npcId={value=10}}}}}}
          assets={source=source,dep={}}
          game={version="1287369|fixture",assets={
            get_resource=function(guid,kind) return assets[guid] end,
            get_resources_by_type=function(kind) return {source} end,
            create_resource=function() error("mutation reached") end}}
        ''')
        from scripts.stage10_10_summarize import fnv
        lua.globals().profile.component_fingerprint = fnv(",".join(sorted((
            "keen::ecs::CharacterSetup", "keen::ecs::AnimationGraphResourceComponent2", "keen::ecs::ActiveNpcState"))))
        return lua

    def test_known_fixture_inspection_never_grants_install(self):
        lua = self.rig()
        result = lua.eval("guard.inspect(game, profile)")
        self.assertFalse(result["spawn_ready"])
        self.assertFalse(result["installation_ready"])
        self.assertEqual(result["writer_status"], "NOT_EXECUTED")


for name, change, error in (
    ("unknown_build", 'game.version="999|fixture"', "UNSUPPORTED_GAME_BUILD"),
    ("missing_version", 'game.version=nil', "UNSUPPORTED_GAME_BUILD"),
    ("no_clean_baseline", 'profile.clean_baseline_verified=false', "clean_baseline_required"),
    ("source_missing", 'assets.source=nil', "source_missing"),
    ("guid_collision", 'assets.clone=source', "custom_guid_collision"),
    ("component_changed", 'profile.component_count=81', "component_schema_changed"),
    ("hashkey_missing", 'setup.hair=nil', "unsupported_hashkey32"),
    ("hashkey_changed", 'setup.hair.value=8', "source_hashkey_changed"),
    ("dependency_missing", 'assets.dep=nil', "resource_dependency_missing"),
    ("npc_collision", 'profile.npc_id=10', "npc_id_collision"),
    ("animation_changed", 'profile.animation_graph="other"', "animation_graph_changed"),
    ("incomplete_profile", 'profile.hashkeys.hair=nil', "incomplete_profile"),
):
    def check(self, change=change, error=error):
        from lupa import LuaError
        lua = self.rig(); lua.execute(change)
        with self.assertRaisesRegex(LuaError, error):
            lua.eval("guard.inspect(game, profile)")
    add_case(LuaPreparationTests, name, check)
