import dataclasses
import tempfile
import unittest
from pathlib import Path

from lupa import LuaRuntime

from companion.eml_humanoid import (
    DESCRIPTOR, EXPECTED_NPC_ID, KNOWN_RESOURCES, PATCH_ID, PATCH_VERSION,
    SOURCE_TEMPLATE_GUID, STORY_TEMPLATE_GUIDS, TEMPLATE_GUID,
    PatchValidationError, guid_id, require_runtime_descriptor, validate_patch,
)


ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "experimental" / "eml_humanoid"


class EmlHumanoidPatchTests(unittest.TestCase):
    def _run_model_case(self, model_component):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(f'''loader = {{ features = {{ patch = true, export = true }} }}
function deepcopy(value)
  if type(value) ~= "table" then return value end
  local copy = {{}}; for k, v in pairs(value) do copy[deepcopy(k)] = deepcopy(v) end; return copy
end
source = {{ guid = "{SOURCE_TEMPLATE_GUID}", data = {{ components = {{
  {{ type = "keen::ecs::Faction", value = {{ faction = "Vukah" }} }},
  {{ type = "keen::ecs::ActiveNpcState", value = {{ npcId = {{ value = 1 }} }} }},
  {model_component}
  {{ type = "keen::ecs::AnimationGraphResourceComponent2", value = {{ animationGraph = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee" }} }}
}} }} }}
registry = {{ data = {{ guids = {{}} }} }}
io.export = function(path, content) exported = content end
game = {{ guid = {{ hash = function() return {EXPECTED_NPC_ID} end }}, assets = {{
  get_resource = function(guid) if guid == "{SOURCE_TEMPLATE_GUID}" then return source else return created end end,
  create_resource = function(value) created = {{data=deepcopy(value)}}; return created end,
  get_resources_by_type = function() return {{registry}} end
}} }}''')
        source = (PATCH / "src" / "mod.lua").read_text(encoding="utf-8").replace(
            "__AIC_STAGE10_RUN_TOKEN__", "0123456789abcdef0123456789abcdef")
        lua.execute(source)
        return str(lua.eval("exported"))

    def test_repository_patch_is_structurally_valid(self):
        checks = validate_patch(PATCH)
        self.assertIn("no_autospawn", checks)
        self.assertIn("safe_faction", checks)

    def test_real_lua_patch_clones_without_mutating_story_source(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute(f'''loader = {{ features = {{ patch = true, export = true }} }}
function deepcopy(value)
  if type(value) ~= "table" then return value end
  local copy = {{}}
  for k, v in pairs(value) do copy[deepcopy(k)] = deepcopy(v) end
  return copy
end
source = {{ guid = "{SOURCE_TEMPLATE_GUID}", data = {{ name = "HunterAssistant", components = {{
  {{ type = "keen::ecs::Faction", value = {{ faction = "Vukah" }} }},
  {{ type = "keen::ecs::ActiveNpcState", value = {{ npcId = {{ value = 1633192162 }} }} }},
  {{ type = "keen::ecs::ModelResource", value = {{ model = "11111111-2222-4333-8444-555555555555" }} }},
  {{ type = "keen::ecs::AnimationGraphResourceComponent2", value = {{ animationGraph = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee" }} }}
}} }} }}
registry = {{ data = {{ guids = {{ "{SOURCE_TEMPLATE_GUID}" }} }} }}
io.export = function(path, content) exported_path = path; exported = content end
game = {{
  guid = {{ hash = function(_) return {EXPECTED_NPC_ID} end }},
  assets = {{
    get_resource = function(guid, typ)
      if guid == "{SOURCE_TEMPLATE_GUID}" and typ == "keen::ecs::TemplateResource" then return source end
      if guid == "{TEMPLATE_GUID}" and typ == "keen::ecs::TemplateResource" then return created end
      return nil
    end,
    create_resource = function(value, typ, guid, part)
      assert(typ == "keen::ecs::TemplateResource" and guid == "{TEMPLATE_GUID}" and part == 0)
      created = {{ data = deepcopy(value) }}
      return created
    end,
    get_resources_by_type = function(typ)
      if typ == "keen::GuidRegistryResource" then return {{ registry }} end
      return {{}}
    end
  }}
}}''')
        patch_source = (PATCH / "src" / "mod.lua").read_text(encoding="utf-8").replace(
            "__AIC_STAGE10_RUN_TOKEN__", "0123456789abcdef0123456789abcdef")
        lua.execute(patch_source)
        self.assertEqual(lua.eval("source.data.components[1].value.faction"), "Vukah")
        self.assertEqual(lua.eval("created.data.components[1].value.faction"), "PlayerAlly")
        self.assertEqual(lua.eval("created.data.components[2].value.npcId.value"), EXPECTED_NPC_ID)
        self.assertEqual(lua.eval("registry.data.guids[2]"), TEMPLATE_GUID)
        self.assertEqual(lua.eval("exported_path"), "aic_eml_humanoid/template_evidence_v3.txt")
        exported = lua.eval("exported")
        self.assertIn("format=aic_eml_humanoid_evidence_v3", exported)
        self.assertIn("fingerprint_hash=", exported)
        self.assertIn("animation_graph_guid=aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee", exported)
        self.assertIn("source_unchanged=true", exported)
        self.assertIn("run_token=0123456789abcdef0123456789abcdef", exported)

    def test_missing_model_component_is_typed_missing(self):
        exported = self._run_model_case("")
        self.assertIn("source_gender_status=MISSING", exported)
        self.assertIn("clone_gender_status=MISSING", exported)

    def test_missing_model_field_is_not_stringified_nil(self):
        exported = self._run_model_case(
            '{ type = "keen::ecs::ModelResource", value = { wrong = "x" } },')
        self.assertIn("format=aic_eml_humanoid_evidence_v3", exported)
        self.assertNotIn("model_value=nil", exported)

    def test_guid_object_and_wrong_reference_type_are_unsupported(self):
        exported = self._run_model_case(
            '{ type = "keen::ecs::ModelResource", value = { model = {} } },')
        self.assertIn("runtime_render_provenance=RUNTIME_RENDER_UNKNOWN", exported)

    def test_game_guid_hash_matches_pinned_survivors_and_new_id(self):
        self.assertEqual(guid_id(SOURCE_TEMPLATE_GUID), 1_633_192_162)
        self.assertEqual(guid_id(TEMPLATE_GUID), EXPECTED_NPC_ID)

    def test_new_guid_is_not_a_story_npc(self):
        self.assertNotIn(TEMPLATE_GUID, STORY_TEMPLATE_GUIDS)
        self.assertIn(SOURCE_TEMPLATE_GUID, STORY_TEMPLATE_GUIDS)

    def test_runtime_is_fail_closed_for_all_current_blockers(self):
        with self.assertRaises(PatchValidationError) as caught:
            require_runtime_descriptor()
        reason = str(caught.exception)
        for blocker in ("runtime_disabled",
                        "animation_graph_unconfirmed", "creation_marker_missing",
                        "ownership_unproven", "safe_dismiss_unproven"):
            self.assertIn(blocker, reason)

    def test_unconfirmed_faction_is_rejected(self):
        bad = dataclasses.replace(DESCRIPTOR, expected_faction=3, runtime_enabled=True)
        with self.assertRaisesRegex(PatchValidationError, "safe_faction_unconfirmed"):
            require_runtime_descriptor(bad)

    def test_unknown_or_conflicting_guid_is_rejected(self):
        with self.assertRaisesRegex(PatchValidationError, "template_guid_conflict"):
            validate_patch(PATCH, occupied_guids={TEMPLATE_GUID})

    def test_unknown_template_guid_is_rejected(self):
        self._mutated(TEMPLATE_GUID, "ffffffff-ffff-4fff-8fff-ffffffffffff",
                      "unknown_template_guid", lua=True)

    def test_story_template_cannot_be_runtime_target(self):
        bad = dataclasses.replace(DESCRIPTOR, template_guid=SOURCE_TEMPLATE_GUID,
                                  runtime_enabled=True)
        with self.assertRaisesRegex(PatchValidationError, "story_npc_template_forbidden"):
            require_runtime_descriptor(bad)

    def test_missing_resource_is_rejected(self):
        with self.assertRaisesRegex(PatchValidationError, "missing_source_resource"):
            validate_patch(PATCH, known_resources=frozenset())

    def test_unsupported_layout_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(PatchValidationError, "unsupported_patch_layout"):
                validate_patch(tmp)

    def test_unsupported_capability_is_rejected(self):
        self._mutated('"capabilities": ["patch", "export"]', '"capabilities": ["runtime"]',
                      "unsupported_capabilities")

    def test_autospawn_is_rejected(self):
        self._mutated("-- Stage 10.6", "spawn()\n-- Stage 10.6",
                      "automatic_spawn_forbidden", lua=True)

    def test_runtime_command_is_rejected(self):
        self._mutated("-- Stage 10.6", "emf.destroy(1)\n-- Stage 10.6",
                      "runtime_command_forbidden", lua=True)

    def test_validation_rejects_missing_safe_faction_marker(self):
        self._mutated('c.value.faction="PlayerAlly"',
                      'c.value.faction="Vukah"', "safe_faction_unconfirmed", lua=True)

    def _mutated(self, old, new, error, *, lua=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            manifest = (PATCH / "mod.json").read_text(encoding="utf-8")
            script = (PATCH / "src" / "mod.lua").read_text(encoding="utf-8")
            if lua:
                script = script.replace(old, new, 1)
            else:
                manifest = manifest.replace(old, new, 1)
            (root / "mod.json").write_text(manifest, encoding="utf-8")
            (root / "src" / "mod.lua").write_text(script, encoding="utf-8")
            with self.assertRaisesRegex(PatchValidationError, error):
                validate_patch(root, known_resources=KNOWN_RESOURCES)


if __name__ == "__main__":
    unittest.main()
