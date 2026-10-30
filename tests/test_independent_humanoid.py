import unittest

from companion.human_body import Evidence
from companion.independent_humanoid import (
    BodyObservation, DESCRIPTORS, HumanBodyDescriptor, HumanoidBlocked,
    IndependentHumanoidGate, Lifecycle, Uniqueness, descriptor,
)


class IndependentHumanoidCatalogTests(unittest.TestCase):
    def test_catalog_contains_only_pinned_unique_survivors(self):
        self.assertEqual(len(DESCRIPTORS), 18)
        self.assertTrue(all(x.uniqueness is Uniqueness.UNIQUE_STORY_NPC for x in DESCRIPTORS.values()))
        self.assertTrue(all(not x.runtime_enabled for x in DESCRIPTORS.values()))

    def test_unknown_humanoid_template_is_rejected(self):
        with self.assertRaisesRegex(HumanoidBlocked, "unknown_humanoid_template"):
            descriptor("imaginary_human")

    def test_unique_npc_and_missing_resources_fail_preflight(self):
        gate = IndependentHumanoidGate(descriptor("hunter_assistant"), session="s1")
        self.assertFalse(gate.preflight())
        self.assertIn("template_not_proven_non_unique", gate.reason)
        self.assertIn("model_guid_unknown", gate.reason)
        self.assertIn("animation_graph_unknown", gate.reason)
        self.assertIn("safe_initial_faction_unknown", gate.reason)

    def test_capabilities_are_evidence_aware_and_disabled(self):
        caps = descriptor("hunter_assistant").capabilities
        self.assertEqual(caps["moveTo"].evidence, Evidence.CONFIRMED)
        self.assertTrue(all(not cap.runtime_enabled for cap in caps.values()))


def verified_descriptor():
    old = descriptor("hunter_assistant")
    return HumanBodyDescriptor(
        key=old.key, template_guid=old.template_guid, source="test-fixture",
        npc_id=old.npc_id, model_guid="model-human", animation_graph_guid="anim-human",
        initial_faction=11, uniqueness=Uniqueness.NON_UNIQUE,
        creation_marker="marker-component", ownership_proof="marker+session",
        safe_dismiss_proven=True, capabilities=old.capabilities, runtime_enabled=True,
    )


class IndependentHumanoidLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.body = verified_descriptor()
        self.gate = IndependentHumanoidGate(self.body, session="s1")
        self.assertTrue(self.gate.preflight())
        self.gate.spawn_requested(entity_id=42, marker="m1", outcome_known=True)
        self.good = BodyObservation("s1", 42, self.body.template_guid, "model-human",
                                    self.body.npc_id, 11, "active_npc", "m1")

    def trust(self):
        for _ in range(3):
            self.gate.observe(self.good)

    def test_incomplete_fingerprint_and_reflection_error_reset_stability(self):
        partial = BodyObservation("s1", 42, self.body.template_guid, None,
                                  self.body.npc_id, 11, "active_npc", "m1")
        self.assertEqual(self.gate.observe(partial), "fingerprint_incomplete")
        self.assertEqual(self.gate.observe(self.good), "fingerprint_stabilizing")
        self.assertEqual(self.gate.observe(None, reflection_error=True), "reflection_error")
        self.assertFalse(self.gate.owned)

    def test_unknown_faction_never_establishes_ownership(self):
        unknown = BodyObservation("s1", 42, self.body.template_guid, "model-human",
                                  self.body.npc_id, None, "active_npc", "m1")
        for _ in range(3):
            self.assertEqual(self.gate.observe(unknown), "fingerprint_incomplete")
        self.assertFalse(self.gate.owned)

    def test_identity_change_and_entity_reuse_latch_recovery(self):
        self.gate.observe(self.good)
        changed = BodyObservation("s1", 43, self.body.template_guid, "model-human",
                                  self.body.npc_id, 11, "active_npc", "m1")
        self.assertEqual(self.gate.observe(changed), "identity_changed")
        self.assertEqual(self.gate.state, Lifecycle.RECOVERY_REQUIRED)
        self.assertEqual(self.gate.observe(self.good), "identity_changed")

    def test_uncertain_spawn_blocks_repeat_spawn(self):
        gate = IndependentHumanoidGate(self.body, session="s1")
        gate.preflight()
        gate.spawn_requested(entity_id=None, marker=None, outcome_known=False)
        self.assertEqual(gate.state, Lifecycle.RECOVERY_REQUIRED)
        with self.assertRaisesRegex(HumanoidBlocked, "preflight_required"):
            gate.spawn_requested(entity_id=44, marker="m2", outcome_known=True)

    def test_unknown_ownership_blocks_dismiss(self):
        with self.assertRaisesRegex(HumanoidBlocked, "current_ownership_unconfirmed"):
            self.gate.begin_dismiss(self.good)

    def test_safe_lifecycle_requires_stable_identity_and_three_absence_samples(self):
        self.trust()
        self.gate.mark_safe_inactive()
        self.gate.activate()
        self.gate.begin_dismiss(self.good)
        self.assertFalse(self.gate.confirm_absent(consecutive_absent=2))
        self.assertTrue(self.gate.confirm_absent(consecutive_absent=3))
        self.assertEqual(self.gate.state, Lifecycle.ABSENT)

    def test_unconfirmed_capability_is_refused_even_when_active(self):
        self.trust()
        self.gate.mark_safe_inactive()
        self.gate.activate()
        with self.assertRaisesRegex(HumanoidBlocked, "capability_not_runtime_verified"):
            self.gate.require_operation("moveTo")
        with self.assertRaisesRegex(HumanoidBlocked, "unknown_humanoid_operation"):
            self.gate.require_operation("invented")

    def test_reload_with_uncertain_entity_never_resumes_or_respawns(self):
        self.gate.reload("s2")
        self.assertEqual(self.gate.state, Lifecycle.RECOVERY_REQUIRED)
        self.assertEqual(self.gate.reason, "reload_with_uncertain_entity")


if __name__ == "__main__":
    unittest.main()
