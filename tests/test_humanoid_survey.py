import json
import unittest
from pathlib import Path

from lupa import LuaRuntime


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mods" / "aic_humanoid_survey"


class HumanoidSurveyTests(unittest.TestCase):
    def test_manifest_is_disabled_and_requires_confirmed_lua_api(self):
        manifest = json.loads((MOD / "mod.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["enabled"])
        self.assertEqual(manifest["emf"], 20)
        self.assertEqual(manifest["depends"]["lua"], ">=1.8")

    def test_diagnostic_source_contains_only_read_paths(self):
        source = (MOD / "main.lua").read_text(encoding="utf-8")
        for forbidden in (
            "emf.spawn", "emf.destroy", "emf.emit", "emf.put", "emf.take",
            "emf.give", "emf.save_world_data", "world:set", "on_tick",
        ):
            self.assertNotIn(forbidden, source)
        for required in ("world.get", "world.template", "world.entities", "world.position"):
            self.assertIn(required, source)

    def test_template_guid_limitation_is_reported(self):
        source = (MOD / "main.lua").read_text(encoding="utf-8")
        self.assertIn("template_guid_available=false", source)
        self.assertIn("read_only=true", source)

    def test_lua_sources_compile(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        compile_lua = lua.eval("load")
        for name in ("main.lua", "json.lua"):
            result = compile_lua((MOD / name).read_text(encoding="utf-8"), name)
            if isinstance(result, tuple):
                self.fail(f"{name}: {result[1]}")
            self.assertTrue(callable(result), name)


if __name__ == "__main__":
    unittest.main()
