import unittest
from pathlib import Path

from companion.human_body import (
    BodyUnavailable, CANDIDATES, Evidence, IdentityGate, IdentityObservation,
    candidate, require_runtime_body,
)


class HumanBodyCatalogTests(unittest.TestCase):
    def test_pinned_survivor_catalog_is_recognized_but_not_runtime_enabled(self):
        self.assertEqual(len(CANDIDATES), 18)
        smith = candidate("blacksmith")
        self.assertEqual(smith.template_guid, "c313f0a8-ed2e-444e-8384-a540f6bbd98e")
        self.assertEqual(smith.npc_id, 1_201_801_546)
        self.assertFalse(smith.runtime_enabled)
        with self.assertRaisesRegex(BodyUnavailable, "human_body_not_runtime_verified"):
            require_runtime_body("blacksmith")
        self.assertTrue(all(not body.runtime_enabled for body in CANDIDATES.values()))

    def test_unknown_template_is_never_selected(self):
        with self.assertRaisesRegex(BodyUnavailable, "unknown_human_body"):
            candidate("Player_Human_Imaginary")

    def test_capabilities_distinguish_engine_evidence_from_implementation(self):
        caps = candidate("hunter").capabilities
        self.assertEqual(caps["moveTo"].evidence, Evidence.CONFIRMED)
        self.assertFalse(caps["moveTo"].implemented)
        for name in ("spawn", "follow", "stay", "attack", "interact", "dismiss",
                     "inventory", "equipment"):
            self.assertFalse(caps[name].implemented, name)

    def test_legacy_vukah_guid_is_not_in_generic_lifecycle_controller(self):
        root = Path(__file__).resolve().parents[1]
        controller = (root / "mods/aic_body/body.lua").read_text(encoding="utf-8")
        profiles = (root / "mods/aic_body/body_profiles.lua").read_text(encoding="utf-8")
        self.assertNotIn("d5d05217-52dc-467a-9192-26b4f661d8d9", controller)
        self.assertIn("legacy_vukah", profiles)


class HumanIdentityGateTests(unittest.TestCase):
    def setUp(self):
        self.body = candidate("blacksmith")
        self.good = IdentityObservation(7001, "world-1", "model-human", self.body.npc_id, "active_npc")

    def gate(self, **kwargs):
        return IdentityGate(self.body, session="world-1", entity_id=7001,
                            model_guid="model-human", **kwargs)

    def test_missing_and_partial_fingerprint_never_become_trusted(self):
        gate = self.gate()
        self.assertEqual(gate.observe(None), "fingerprint_incomplete")
        partial = IdentityObservation(7001, "world-1", None, self.body.npc_id, "active_npc")
        self.assertEqual(gate.observe(partial), "fingerprint_incomplete")
        self.assertFalse(gate.trusted)
        self.assertFalse(gate.deletable)

    def test_delayed_components_require_three_consecutive_complete_samples(self):
        gate = self.gate()
        gate.observe(None)
        self.assertEqual(gate.observe(self.good), "fingerprint_stabilizing")
        self.assertEqual(gate.observe(self.good), "fingerprint_stabilizing")
        self.assertEqual(gate.observe(self.good), "trusted")
        self.assertTrue(gate.trusted)

    def test_reflection_error_resets_stability_and_times_out_closed(self):
        gate = self.gate(acquisition_limit=4)
        gate.observe(self.good)
        self.assertEqual(gate.observe(None, reflection_error=True), "reflection_error")
        gate.observe(None, reflection_error=True)
        self.assertEqual(gate.observe(None, reflection_error=True), "fingerprint_timeout")
        self.assertTrue(gate.invalidated)
        self.assertFalse(gate.deletable)

    def test_identity_change_and_entity_id_reuse_are_latched(self):
        gate = self.gate()
        for _ in range(3):
            gate.observe(self.good)
        reused = IdentityObservation(7002, "world-1", "model-human", self.body.npc_id, "active_npc")
        self.assertFalse(gate.permits_delete(reused))
        self.assertTrue(gate.invalidated)
        self.assertEqual(gate.observe(self.good), "identity_changed")

    def test_unknown_expected_model_blocks_trust_and_delete(self):
        gate = IdentityGate(self.body, session="world-1", entity_id=7001, model_guid=None)
        for _ in range(5):
            self.assertEqual(gate.observe(self.good), "blocked")
        self.assertFalse(gate.trusted)
        self.assertFalse(gate.permits_delete(self.good))

    def test_delete_requires_a_current_exact_observation(self):
        gate = self.gate()
        for _ in range(3):
            gate.observe(self.good)
        self.assertTrue(gate.permits_delete(self.good))
        changed = IdentityObservation(7001, "world-1", "other-model", self.body.npc_id, "active_npc")
        self.assertFalse(gate.permits_delete(changed))


if __name__ == "__main__":
    unittest.main()
