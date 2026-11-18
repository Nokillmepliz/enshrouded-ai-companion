"""Repeat pinned, read-only KFC queries; retain proprietary dumps only in runtime.

No writer, patcher, game process or bridge is invoked. The inspector refuses
outputs inside the game directory and refuses overwrite.
"""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "runtime/research/stage10_5"
OUT = ROOT / "runtime/stage10_10/resources"
GAME = r"D:\SteamLibrary\steamapps\common\Enshrouded"
INSPECTOR = ROOT / ".tools/kfc-inspector/bin/kfc-readonly-inspect.exe"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    files = [OLD / name for name in ("hunter_assistant.json", "blacksmith_assistant.json",
             "character_preset_collection.json", "item_registry.json", "humanoid_hierarchy.json")]
    files += sorted((OLD / "render_models").glob("*.json"))
    files += sorted((OLD / "related_item_info").glob("*.json"))
    # Decode known reference resources again against the installed EXE's schema.
    for old in files:
        data = json.loads(old.read_text(encoding="utf-8"))
        target = OUT / old.name
        proc = subprocess.run([str(INSPECTOR), GAME, data["guid"], data["type"], str(target)],
                              capture_output=True, text=True, timeout=180)
        if proc.returncode:
            raise RuntimeError(f"decode_failed:{old.name}:{proc.stderr[:400]}")
        current = json.loads(target.read_text(encoding="utf-8"))
        records.append({"resource": old.name, "guid": data["guid"], "type": data["type"],
                        "equal_to_1273043": data["resource"] == current["resource"]})
    clone = OUT / "clone.json"
    subprocess.run([str(INSPECTOR), GAME, "a1c90001-5e4d-4a91-8a1c-000000000001",
                    "keen::ecs::TemplateResource", str(clone)], check=True, timeout=180)
    (OUT.parent / "resource-comparison.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(json.dumps({"resources": len(records), "unchanged": sum(r["equal_to_1273043"] for r in records),
                      "changed": [r["resource"] for r in records if not r["equal_to_1273043"]]}))


if __name__ == "__main__":
    main()
