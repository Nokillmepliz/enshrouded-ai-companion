import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from companion.client import BodyClient, ClientError
from companion import profile
from companion.__main__ import main
from companion.transport import BRIDGE_SHA256
from tests.test_body import BodyRig, ROOT


class BridgeFake:
    """End-to-end client -> console wire -> real Lua adapter -> fake game."""
    def __init__(self):
        self.rig = BodyRig()
        self.calls = []
        self.now = 0
        self.hello_data = {"ok": True, "emf": "0.3.2", "api": 20, "protocol": 1,
                           "game_build": 1273043, "process": "client", "pid": 42}
        self.state_data = {"ok": True, "world": {"kind": "server", "status": "running", "slot": 1},
                           "character": {"storage": "local", "slot": 2, "name": "Body Test"},
                           "player": {"id": 1}}
        self.mangle = None

    def hello(self):
        return copy.deepcopy(self.hello_data)

    def state(self):
        return copy.deepcopy(self.state_data)

    def console(self, text, **kwargs):
        self.calls.append(text)
        name, *args = text.split()
        raw = self.rig.fake.command(name.split('.')[1], self.rig.lua.table_from(args))
        response = {"ok": True, "status": "ran", "output": [raw]}
        return self.mangle(response) if self.mangle else response

    def sleep(self, amount):
        self.now += amount
        self.rig.step(12)


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.bridge = BridgeFake()
        self.client = BodyClient(self.bridge, clock=lambda: self.bridge.now, sleep=self.bridge.sleep)
        self.options = dict(allow_mutations=True, world_slot=1, character_slot=2,
                            character_name="Body Test", request_id="client_req")

    def execute(self, action="spawn", **overrides):
        return self.client.execute(action, "companion1", **(self.options | overrides))

    def assert_code(self, code, callback):
        with self.assertRaises(ClientError) as caught:
            callback()
        self.assertEqual(caught.exception.code, code)

    def test_complete_spawn_stay_follow_dismiss_over_real_lua(self):
        self.assertEqual(self.execute()["request"]["status"], "succeeded")
        for action in ("stay", "follow", "dismiss"):
            self.assertEqual(self.execute(action, request_id=action)["request"]["status"], "succeeded")
        self.assertEqual(self.client.status()["state"]["mode"], "absent")

    def test_no_permission_means_no_connection_calls(self):
        self.assert_code("game_mutations_not_authorized", lambda: self.execute(allow_mutations=False))
        self.assertEqual(self.bridge.calls, [])

    def test_cloud_character_refused_before_mutating_console(self):
        self.bridge.state_data["character"]["storage"] = "steam"
        self.assert_code("wrong_test_character", self.execute)
        self.assertFalse(any(".request" in c for c in self.bridge.calls))

    def test_cloud_world_and_remote_host_and_wrong_name_refused(self):
        for world in ({"slot": 65537}, {"kind": "client"}, {"status": "loading"}):
            with self.subTest(world=world):
                original = self.bridge.state_data["world"].copy()
                self.bridge.state_data["world"].update(world)
                self.assert_code("wrong_test_world", self.execute)
                self.bridge.state_data["world"] = original
        self.assert_code("wrong_test_character", lambda: self.execute(character_name="Main Hero"))
        self.assertEqual(self.bridge.rig.fake.spawns, 0)

    def test_unknown_build_refused(self):
        self.bridge.hello_data["game_build"] = "unknown"
        self.assert_code("unsupported_game_build_or_process", self.execute)
        self.assertEqual(self.bridge.rig.fake.spawns, 0)

    def test_world_change_during_preflight_cannot_spawn(self):
        original = self.bridge.state
        def switched():
            self.bridge.rig.fake.session = "different-2"
            return original()
        self.bridge.state = switched
        self.assert_code("stale_epoch", self.execute)
        self.assertEqual(self.bridge.rig.fake.spawns, 0)

    def test_timeout_is_unknown_not_retried_or_success(self):
        self.bridge.rig.fake.drop_events = True
        self.assert_code("verification_timeout_outcome_unknown", lambda: self.execute(timeout=0.4))
        self.assertEqual(len([c for c in self.bridge.calls if '.request' in c]), 1)
        self.assertEqual(self.bridge.rig.fake.spawns, 1)

    def test_bridge_disconnect_does_not_replay_mutation(self):
        original = self.bridge.console
        def disconnect(text, **kwargs):
            result = original(text, **kwargs)
            if '.request' in text:
                raise OSError("connection lost after request")
            return result
        self.bridge.console = disconnect
        self.assert_code("bridge_error_outcome_unknown", self.execute)
        self.assertEqual(self.bridge.rig.fake.spawns, 1)

    def test_missing_or_malformed_reply_rejected(self):
        for output, code in (([], "adapter_reply_missing_or_ambiguous"),
                             (["AIC_BODY {"], "malformed_adapter_json"),
                             (["AIC_BODY {}"], "unsupported_adapter_protocol")):
            self.bridge.mangle = lambda r, output=output: r | {"output": output}
            self.assert_code(code, self.client.status)

    def test_bad_request_correlation_rejected(self):
        def mangle(r):
            data = json.loads(r["output"][0][9:])
            if "request" in data:
                data["request"]["id"] = "wrong"
            return r | {"output": ["AIC_BODY " + json.dumps(data)]}
        self.bridge.mangle = mangle
        self.assert_code("request_correlation_failed", self.execute)

    def test_status_no_mutations_and_diagnose_disconnected_body(self):
        self.client.diagnose()
        self.assertEqual(self.bridge.rig.fake.spawns, 0)
        self.bridge.mangle = lambda r: r | {"status": "unknown"}
        self.assertEqual(self.client.diagnose()["body_error"]["code"], "console_refused")

    def test_injection_and_unsupported_actions_refused(self):
        self.assert_code("invalid_token", lambda: self.execute(request_id="x\nspawn"))
        self.assert_code("unsupported_action", lambda: self.execute("attack"))
        self.assertEqual(self.bridge.rig.fake.spawns, 0)

    def test_cli_no_flag_does_not_open_transport(self):
        with patch("companion.transport.connect") as connect, contextlib.redirect_stderr(io.StringIO()):
            code = main(["spawn", "--pid", "42", "--world-slot", "1", "--character-slot", "2",
                         "--character-name", "Body Test"])
        self.assertEqual(code, 1)
        connect.assert_not_called()

    def test_vendored_bridge_matches_reviewed_file(self):
        self.assertEqual(hashlib.sha256((ROOT / "vendor/emf_bridge.py").read_bytes()).hexdigest(), BRIDGE_SHA256)


class ProfileTests(unittest.TestCase):
    def test_identity_survives_client_restarts_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "personality.json"
            created = profile.create(path, "Друг")
            self.assertEqual(created, profile.load(path))
            self.assertEqual(set(created), {"schema", "name", "companion_id", "personality"})
            with self.assertRaises(FileExistsError):
                profile.create(path, "Другой")
            self.assertEqual(profile.load(path)["companion_id"], created["companion_id"])

    def test_runtime_id_rejected_in_personality(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.json"
            data = profile.create(path, "Друг")
            with self.assertRaises(ValueError):
                profile.validate(data | {"entity_id": 100})


if __name__ == "__main__":
    unittest.main()
