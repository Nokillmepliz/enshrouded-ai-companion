"""Load the pinned upstream Windows bridge only for explicit live commands."""
import hashlib
import importlib.util
import os
from pathlib import Path

BRIDGE_SHA256 = "7c6ca431231dd3628cf2ccf80abe45359e564354afd95c6001628511e88b2b75"


def connect(*, game=None, pid=None):
    if os.name != "nt":
        raise RuntimeError("Live EMF bridge requires Windows")
    if not game and not pid:
        raise ValueError("An explicit --game folder or --pid is required")
    path = Path(__file__).resolve().parents[1] / "vendor" / "emf_bridge.py"
    if hashlib.sha256(path.read_bytes()).hexdigest() != BRIDGE_SHA256:
        raise RuntimeError("Vendored bridge hash mismatch; restore the pinned file")
    spec = importlib.util.spec_from_file_location("aic_upstream_bridge", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module.Bridge(game=game, pid=pid, connect_timeout=3)
    except (module.ConnectError, module.BridgeError) as exc:
        raise RuntimeError("EMF bridge connection failed: " + str(exc)) from exc
