"""Publish metadata/hashes only from ignored offline research; never raw resources."""
import json
from collections import Counter
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from companion.compatibility import classify_file, compare_schema, file_hash, fingerprint
from tools.reflection_schema import parse_reflection

WORK = ROOT / "runtime/stage10_10"
OUT = ROOT / "compatibility/audits/1287369"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def schemas(path):
    data = parse_reflection(path)
    hashes = dict(re.findall(r'\{"([^"]+)", "[^"]+", 0x([0-9a-f]+)u,', path.read_text()))
    return {k: {**v, "hash": hashes[k]} for k, v in data.items()}


def fnv(text):
    h = 2166136261
    for c in text.encode():
        h = ((h ^ c) * 16777619) & 0xffffffff
    return f"{h:08x}"


def diff_paths(a, b, path=""):
    if type(a) is not type(b):
        return [path]
    if isinstance(a, dict):
        return [p for k in sorted(a.keys() | b.keys()) for p in
                ([path + "/" + k] if k not in a or k not in b else diff_paths(a[k], b[k], path + "/" + k))]
    if isinstance(a, list):
        return [path + "/length"] if len(a) != len(b) else [p for i, (x, y) in enumerate(zip(a, b)) for p in diff_paths(x, y, path + f"/{i}")]
    return [] if a == b else [path]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before = read(WORK / "before.json")
    old_pre = read(ROOT / "runtime/stage10_7/phase-c-preflight.json")
    old_post = read(ROOT / "runtime/stage10_7/evidence/post-run-integrity.json")
    receipt = read(ROOT / "runtime/stage10_7/install-receipt.json")
    previous = {}
    # Stage 10.7 has exact digests only for selected files, not a full inventory.
    for name, entry in old_pre["dat"].items():
        previous[name] = entry["sha256"] if isinstance(entry, dict) else entry
    previous.update({"enshrouded.kfc": old_post["kfc"]["current_sha256"],
                     "enshrouded.kfc_resources": old_post["kfc_resources"]["current_sha256"],
                     "enshrouded.kfc.bak": old_post["kfc"]["bak_sha256"]})
    artifacts = {x["path"]: x["sha256"] for x in receipt["applied"]}
    artifacts["dinput8.dll"] = "53b3f6ebebd2730234a882ddd00b09e72d32cb32c21a1fcdfb5a86a205f6dbee"
    for x in old_post["dat"]["added"]:
        artifacts[x["name"]] = x["sha256"]
    previous.update(artifacts)
    previous["enshrouded.exe"] = "d64966e23b1a458ee6f147bcbceac0b577fa7e39a212f371287d8cc119817882"
    records = []
    for name in sorted(before["game"].keys() | previous.keys()):
        item = before["game"].get(name, {})
        current = item.get("sha256")
        official = "5d9ef2f140b8ed49e30dbee655841b89d08baec20f799a1817e171a18a850c77" if name == "enshrouded.exe" else None
        status = classify_file(current, previous.get(name), artifact=artifacts.get(name), official=official)
        provenance = "stage10_7_exact_hash" if name in previous else "no_previous_per_file_digest"
        if name == "dinput8.dll":
            provenance = "historical_EMF_0.3.2_loader_audit_exact_hash"
        # NEW means new to this inventory, not proven created by Steam.
        records.append({"path": name, "bytes": item.get("bytes"), "sha256": current,
                        "previous_sha256": previous.get(name), "status": status, "provenance": provenance})
    write("file-inventory.json", {"format": "aic_offline_file_inventory_v1", "game_build": 1287369,
          "clean_baseline": False, "counts": dict(Counter(x["status"] for x in records)), "files": records})
    write("cleanup-candidates.json", {"format": "aic_cleanup_review_candidates_v1", "executable": False,
          "reason": "Phase B needs separate reviewed ownership and current-build baseline; DAT names are not ownership",
          "files": [x for x in records if x["status"] == "PREVIOUS_MOD_ARTIFACT"]})
    backups = []
    for manifest in sorted((ROOT / "runtime/backups").glob("*/manifest.json")):
        data = read(manifest)
        entries = data["entries"]
        items = ([(manifest.parent / k, v) for k, v in entries.items()] if isinstance(entries, dict)
                 else [(Path(x["backup"]), x) for x in entries])
        passed = sum(p.is_file() and p.stat().st_size == v["bytes"] and file_hash(p) == v["sha256"] for p, v in items)
        backups.append({"name": manifest.parent.name, "manifest_sha256": file_hash(manifest),
                        "files": len(items), "verified_now": passed,
                        "embedded_game_identity": data.get("game_identity"),
                        "historical_build": 1273043, "build_provenance": "dated_project_reports; not embedded in manifest",
                        "restore_to_1287369": "ROLLBACK_BLOCKED_BUILD_MISMATCH"})
    write("backup-audit.json", {"backups": backups, "receipt_sha256": file_hash(ROOT / "runtime/stage10_7/install-receipt.json"),
          "receipt_build": receipt["game_build"], "receipt_files_verified": sum(before["game"].get(x["path"], {}).get("sha256") == x["sha256"] for x in receipt["applied"])})
    old = schemas(ROOT / ".research/emf-enshrouded/sdk/include/emf/generated/reflection.hpp")
    generated = schemas(ROOT / ".research/emf-stage10-10/sdk/include/emf/generated/reflection.hpp")
    actual = schemas(WORK / "generated/reflection.hpp")
    types = read(WORK / "installed-types.emf.json")["types"]
    by_name = {t["qualified_name"]: t for t in types}
    rows = []
    critical = {"EntityId", "CurrentTransform", "CharacterSetup", "Faction", "PlayerState",
                "ActiveNpcState", "ActiveNpcStateSaved", "ForceSave", "DoNotSave", "RenderEquipment",
                "AnimationGraphResourceComponent2", "Movement", "PathWalker", "MovementColliderConfig",
                "Enemy01BehaviorState", "CombatSetup", "Inventory", "HashKey32"}
    for name in sorted(old.keys() | actual.keys()):
        a, b = old.get(name), actual.get(name)
        status = compare_schema(a, b)
        # Avoid publishing two copies of thousands of unchanged upstream fields.
        # Critical/changed fields remain explicit; other identical schemas are hashed.
        def summary(value):
            if value is None or status != "IDENTICAL" or name.split("::")[-1] in critical:
                return value
            return {"hash": value["hash"], "size": value["size"], "field_count": len(value["fields"]),
                    "fields_sha256": fingerprint(value["fields"])}
        rows.append({"name": name, "status": status, "old": summary(a), "new": summary(b),
                     "installed_alignment": by_name.get(name, {}).get("alignment"),
                     "alignment_comparison": "UNKNOWN: old header packed, original alignment unavailable",
                     "current_upstream_generated_match": generated.get(name) == b})
    write("ecs-diff.json", {"format": "aic_generated_ecs_diff_v1", "old_build": 1273043,
          "new_build": 1287369, "scope": "generated field/layout/hash metadata; not all 12658 reflected types",
          "counts": dict(Counter(r["status"] for r in rows)), "types": rows})
    observed = {}
    for label in ("hunter_assistant", "blacksmith_assistant", "clone"):
        resource = read(WORK / "resources" / (label + ".json"))["resource"]
        comps = {v["$type"]: v["$value"] for v in resource["components"]}
        names = ",".join(sorted(comps))
        result = {"component_count": len(comps), "component_fingerprint_fnv32": fnv(names),
                  "canonical_resource_sha256": fingerprint(resource),
                  "character_setup": comps.get("keen::ecs::CharacterSetup"),
                  "animation": comps.get("keen::ecs::AnimationGraphResourceComponent2"),
                  "faction": comps.get("keen::ecs::Faction"),
                  "npc_id": comps.get("keen::ecs::ActiveNpcState", {}).get("npcId"),
                  "persistence_components": [k for k in comps if any(s in k for s in ("ForceSave", "DoNotSave", "ActiveNpc"))]}
        if label != "clone":
            prior = read(ROOT / "runtime/research/stage10_5" / (label + ".json"))["resource"]
            old_comps = {v["$type"]: v["$value"] for v in prior["components"]}
            result["added_components"] = sorted(comps.keys() - old_comps.keys())
            result["removed_components"] = sorted(old_comps.keys() - comps.keys())
            result["changed_fields"] = {k: diff_paths(old_comps[k], comps[k]) for k in old_comps.keys() & comps.keys() if old_comps[k] != comps[k]}
        observed[label] = result
    collection = read(WORK / "resources/character_preset_collection.json")["resource"]
    old_collection = read(ROOT / "runtime/research/stage10_5/character_preset_collection.json")["resource"]
    pick = lambda c: next(x for x in c["presets"] if x["presetId"]["value"] == 1602195472)
    observed["hunter_preset_unchanged"] = pick(collection) == pick(old_collection)
    observed["resource_comparison"] = read(WORK / "resource-comparison.json")
    observed["clean_baseline"] = False
    observed["clone_collision"] = "PRESENT_IN_MODIFIED_DATABASE; clean database not available"
    write("resource-diff.json", observed)
    write("release-files.json", read(WORK / "archive-inventory.json"))
    print(json.dumps({"inventory": Counter(r["status"] for r in records),
                      "backups": [(b["name"], b["verified_now"], b["files"]) for b in backups],
                      "ecs": Counter(r["status"] for r in rows),
                      "hunter": observed["hunter_assistant"]["component_fingerprint_fnv32"],
                      "clone_components": observed["clone"]["component_count"]}))


if __name__ == "__main__":
    main()
