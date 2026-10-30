import unittest

from companion.human_body import Evidence
from companion.player_character import (
    COMMANDS, REQUIRED_PLAYER_COMPONENTS, VARIANTS, PlayerBodyUnavailable,
    PlayerCompanionGate, PlayerObservation, Variant, recommended_variant,
)


class VariantAssessmentTests(unittest.TestCase):
    def test_variants_do_not_overstate_runtime_support(self):
        self.assertEqual(VARIANTS[Variant.IN_PROCESS_PLAYER].evidence, Evidence.UNSUPPORTED)
        self.assertEqual(VARIANTS[Variant.CHARACTER_REPLICA].evidence, Evidence.UNKNOWN)
        self.assertEqual(VARIANTS[Variant.SECOND_CLIENT].evidence, Evidence.LIKELY)
        self.assertFalse(VARIANTS[Variant.CHARACTER_REPLICA].real_player)
        self.assertEqual(recommended_variant(), Variant.SECOND_CLIENT)

    def test_no_command_is_runtime_enabled_without_a_verified_backend(self):
        self.assertEqual(COMMANDS["observe"].evidence, Evidence.CONFIRMED)
        self.assertTrue(all(not command.runtime_enabled for command in COMMANDS.values()))
        for required in ("moveTo", "follow", "stay", "attack", "interact", "equip"):
            self.assertIn(required, COMMANDS)


class PlayerCompanionGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = PlayerCompanionGate(
            session_token="run:world:1", host_entity_id=1,
            host_account_key="0xhost", companion_account_key="0xcompanion",
        )
        self.good = PlayerObservation(
            session_token="run:world:1", entity_id=2, account_key="0xcompanion",
            player_slot=1, connected=True, network_peer_confirmed=True,
            components=REQUIRED_PLAYER_COMPONENTS,
        )

    def test_requires_stable_distinct_player_binding(self):
        self.assertEqual(self.gate.observe(self.good), "identity_stabilizing")
        self.assertEqual(self.gate.observe(self.good), "identity_stabilizing")
        self.assertEqual(self.gate.observe(self.good), "trusted_identity")
        self.assertTrue(self.gate.trusted_identity)
        self.assertFalse(self.gate.runtime_control_enabled)

    def test_main_character_cannot_be_selected_as_companion(self):
        collision = PlayerObservation(
            "run:world:1", 1, "0xcompanion", 1, True, True,
            REQUIRED_PLAYER_COMPONENTS,
        )
        self.assertEqual(self.gate.observe(collision), "host_companion_identity_collision")
        self.assertTrue(self.gate.invalidated)

    def test_unknown_network_authority_never_becomes_trusted(self):
        unknown = PlayerObservation(
            "run:world:1", 2, "0xcompanion", 1, True, False,
            REQUIRED_PLAYER_COMPONENTS,
        )
        for _ in range(5):
            self.assertEqual(self.gate.observe(unknown), "network_authority_unknown")
        self.assertFalse(self.gate.trusted_identity)

    def test_missing_player_component_resets_stability(self):
        self.gate.observe(self.good)
        partial = PlayerObservation(
            "run:world:1", 2, "0xcompanion", 1, True, True,
            REQUIRED_PLAYER_COMPONENTS - {"PlayerInput"},
        )
        self.assertEqual(self.gate.observe(partial), "player_components_missing")
        self.assertFalse(self.gate.trusted_identity)

    def test_account_session_and_entity_changes_latch_closed(self):
        changed = PlayerObservation(
            "run:world:1", 2, "0xother", 1, True, True,
            REQUIRED_PLAYER_COMPONENTS,
        )
        self.assertEqual(self.gate.observe(changed), "account_identity_changed")
        self.assertEqual(self.gate.observe(self.good), "account_identity_changed")

    def test_session_change_latches_closed(self):
        changed = PlayerObservation(
            "run:world:2", 2, "0xcompanion", 1, True, True,
            REQUIRED_PLAYER_COMPONENTS,
        )
        self.assertEqual(self.gate.observe(changed), "session_changed")
        self.assertFalse(self.gate.trusted_identity)

    def test_entity_or_slot_rebinding_after_observation_latches_closed(self):
        self.gate.observe(self.good)
        rebound = PlayerObservation(
            "run:world:1", 3, "0xcompanion", 2, True, True,
            REQUIRED_PLAYER_COMPONENTS,
        )
        self.assertEqual(self.gate.observe(rebound), "player_binding_changed")
        self.assertTrue(self.gate.invalidated)

    def test_disconnect_invalidates_binding_to_prevent_entity_id_reuse(self):
        self.gate.observe(self.good)
        disconnected = PlayerObservation(
            "run:world:1", 2, "0xcompanion", 1, False, True,
            REQUIRED_PLAYER_COMPONENTS,
        )
        self.assertEqual(self.gate.observe(disconnected), "player_not_connected")
        self.assertFalse(self.gate.trusted_identity)
        self.assertTrue(self.gate.invalidated)
        self.assertEqual(self.gate.observe(self.good), "player_not_connected")

    def test_runtime_operations_remain_refused_after_identity_trust(self):
        for _ in range(3):
            self.gate.observe(self.good)
        for operation in COMMANDS:
            with self.assertRaisesRegex(PlayerBodyUnavailable, "control_backend_not_verified"):
                self.gate.require_runtime_control(operation)
        with self.assertRaisesRegex(PlayerBodyUnavailable, "unknown_player_body_operation"):
            self.gate.require_runtime_control("invented_api")

    def test_runtime_operation_requires_trusted_identity_first(self):
        with self.assertRaisesRegex(PlayerBodyUnavailable, "identity_not_trusted"):
            self.gate.require_runtime_control("moveTo")

    def test_same_account_is_rejected_at_configuration_time(self):
        with self.assertRaisesRegex(ValueError, "distinct_account"):
            PlayerCompanionGate(
                session_token="s", host_entity_id=1,
                host_account_key="same", companion_account_key="same",
            )


if __name__ == "__main__":
    unittest.main()
