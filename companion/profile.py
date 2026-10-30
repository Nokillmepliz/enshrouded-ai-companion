"""Stable personality, deliberately independent of world/session/entity IDs."""
import json
from pathlib import Path
from uuid import UUID, uuid4


def validate(profile):
    if not isinstance(profile, dict) or set(profile) != {"schema", "companion_id", "name", "personality"}:
        raise ValueError("Invalid profile fields; runtime entity IDs must not be stored here")
    if (profile["schema"] != 1 or not isinstance(profile["companion_id"], str)
            or str(UUID(profile["companion_id"])) != profile["companion_id"]):
        raise ValueError("Unsupported profile schema or companion UUID")
    if not isinstance(profile["name"], str) or not 1 <= len(profile["name"]) <= 100:
        raise ValueError("Profile name must contain 1..100 characters")
    if not isinstance(profile["personality"], dict):
        raise ValueError("personality must be an object")
    return profile


def create(path, name):
    profile = validate({"schema": 1, "companion_id": str(uuid4()), "name": name,
                        "personality": {"description": "Спокойный спутник исследователя"}})
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation: never silently replace an established identity.
    with target.open("x", encoding="utf-8") as stream:
        json.dump(profile, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return profile


def load(path):
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))
