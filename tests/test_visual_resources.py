import tempfile
import unittest
from pathlib import Path

from companion.visual_fingerprint import (
    VISUAL_COMPONENTS, VisualFingerprintError, assess_visual_pair, canonical_fingerprint,
)
from tools.reflection_schema import parse_reflection
from tools.kfc_readonly_inspect.preflight import InspectorPreflightError, inspect_plan


ROOT = Path(__file__).resolve().parents[1]
REFLECTION = ROOT / "tests/fixtures/reflection_visual.hpp"


def template(**changes):
    value = {
        "template_guid": "e3736dff-0ad2-47fc-903c-66c1775836e8",
        "components": list(VISUAL_COMPONENTS),
        "resource_references_complete": False,
        "resource_references": [],
    }
    value.update(changes)
    return value


class ReflectionSchemaTests(unittest.TestCase):
    def test_confirmed_visual_component_fields_and_types(self):
        schema = parse_reflection(REFLECTION)
        render = {field["name"]: field for field in schema["keen::ecs::RenderEquipment"]["fields"]}
        self.assertEqual((render["modelHandles"]["kind"], render["modelHandles"]["count"]), ("U32", 24))
        self.assertEqual((render["lastModels"]["kind"], render["lastModels"]["count"]), ("Guid", 24))
        character = {field["name"]: field for field in schema["keen::ecs::CharacterSetup"]["fields"]}
        self.assertEqual(character["gender"]["kind"], "U8")
        self.assertEqual(character["presetId"]["nested_type"], "keen::HashKey32")
        self.assertEqual(schema["keen::ecs::NewCharacterSetup"]["fields"], [])
        self.assertEqual(schema["keen::ecs::EquipmentCheck"]["fields"], [])
        graph = {field["name"]: field for field in schema[
            "keen::ecs::AnimationGraphResourceComponent2"]["fields"]}
        self.assertEqual(graph["animationGraph"]["kind"], "Guid")
        self.assertEqual(graph["retargetData"]["kind"], "Guid")

    def test_missing_type_is_explicitly_absent(self):
        self.assertNotIn("keen::ecs::NotARealVisualType", parse_reflection(REFLECTION))

    def test_corrupt_reflection_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reflection.hpp"
            path.write_text("not reflection", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "reflection_array_missing"):
                parse_reflection(path)


class VisualFingerprintTests(unittest.TestCase):
    def test_structural_match_does_not_claim_resources_or_runtime(self):
        result = assess_visual_pair(template(), template(
            template_guid="a1c90001-5e4d-4a91-8a1c-000000000001"))
        self.assertTrue(result["levels"]["STRUCTURAL_MATCH"])
        self.assertIsNone(result["levels"]["RESOURCE_REFERENCES_MATCH"])
        self.assertIsNone(result["levels"]["VISUAL_DEPENDENCIES_RESOLVED"])
        self.assertIsNone(result["levels"]["RUNTIME_RENDER_CONFIRMED"])
        self.assertFalse(result["spawn_ready"])

    def test_missing_component_fails_structural_level(self):
        clone = template(components=list(VISUAL_COMPONENTS[:-1]))
        self.assertFalse(assess_visual_pair(template(), clone)["levels"]["STRUCTURAL_MATCH"])

    def test_confirmed_reference_match_still_needs_resolution(self):
        refs = ["402df515-5965-4b01-a17b-17d482a91af4"]
        source = template(resource_references_complete=True, resource_references=refs)
        clone = template(resource_references_complete=True, resource_references=refs)
        result = assess_visual_pair(source, clone)
        self.assertTrue(result["levels"]["RESOURCE_REFERENCES_MATCH"])
        self.assertIsNone(result["levels"]["VISUAL_DEPENDENCIES_RESOLVED"])
        resolved = assess_visual_pair(source, clone, resolved={refs[0]: True})
        self.assertTrue(resolved["levels"]["VISUAL_DEPENDENCIES_RESOLVED"])

    def test_mismatch_unknown_type_and_missing_guid_fail_closed(self):
        first = ["402df515-5965-4b01-a17b-17d482a91af4"]
        second = ["11111111-2222-4333-8444-555555555555"]
        self.assertFalse(assess_visual_pair(
            template(resource_references_complete=True, resource_references=first),
            template(resource_references_complete=True, resource_references=second),
        )["levels"]["RESOURCE_REFERENCES_MATCH"])
        for bad in ([], ["missing-guid"], [123]):
            with self.subTest(value=bad), self.assertRaises(VisualFingerprintError):
                assess_visual_pair(
                    template(resource_references_complete=True, resource_references=bad), template())

    def test_serialization_is_stable(self):
        left = {"b": [2, 1], "a": {"x": True}}
        right = {"a": {"x": True}, "b": [2, 1]}
        self.assertEqual(canonical_fingerprint(left), canonical_fingerprint(right))


class ReadOnlyInspectorSourceTests(unittest.TestCase):
    def test_inspector_is_pinned_and_has_no_kfc_write_path(self):
        root = ROOT / "tools/kfc_readonly_inspect"
        manifest = (root / "Cargo.toml").read_text(encoding="utf-8")
        source = (root / "src/main.rs").read_text(encoding="utf-8")
        self.assertIn("16708594d686b030d909f2d835b199d879ea9ad8", manifest)
        self.assertIn("KFCReader", source)
        for forbidden in ("KFCWriter", "set_resources", "write_resource", "create_resource"):
            self.assertNotIn(forbidden, source)
        self.assertIn("refusing to write inside game directory", source)
        self.assertIn("refusing to overwrite output", source)

    def test_no_binary_is_published(self):
        root = ROOT / "tools/kfc_readonly_inspect"
        self.assertFalse(any(path.suffix.lower() in {".exe", ".dll"} for path in root.rglob("*")))

    def test_preflight_rejects_corrupt_kfc_and_game_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            game.mkdir()
            (game / "enshrouded.exe").write_bytes(b"exe")
            (game / "enshrouded.kfc_resources").write_bytes(b"resources")
            (game / "enshrouded.kfc").write_bytes(b"corrupt")
            with self.assertRaisesRegex(InspectorPreflightError, "kfc_header_truncated"):
                inspect_plan(game)
            (game / "enshrouded.kfc").write_bytes(
                b"KFC4" + (12).to_bytes(4, "little") + (12).to_bytes(4, "little"))
            with self.assertRaisesRegex(InspectorPreflightError, "output_inside_game_forbidden"):
                inspect_plan(game, game / "report.json")

    def test_preflight_never_modifies_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp) / "game"
            game.mkdir()
            inputs = {
                "enshrouded.exe": b"exe",
                "enshrouded.kfc_resources": b"resources",
                "enshrouded.kfc": b"KFC4" + (12).to_bytes(4, "little") + (12).to_bytes(4, "little"),
            }
            for name, data in inputs.items():
                (game / name).write_bytes(data)
            before = {name: (game / name).read_bytes() for name in inputs}
            result = inspect_plan(game)
            self.assertIn(result["status"], {"READY_TO_BUILD", "BLOCKED_TOOLCHAIN"})
            self.assertFalse(result["writes_performed"])
            self.assertEqual(before, {name: (game / name).read_bytes() for name in inputs})


if __name__ == "__main__":
    unittest.main()
