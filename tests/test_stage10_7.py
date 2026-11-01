import pathlib
import unittest

from companion.stage10_7 import (FORMAT, HASH_FIELDS, UINT32_MAX, decode_hashkey32,
                                  evaluate, parse_evidence, EvidenceV4Error)
from companion.eml_humanoid import (EXPECTED_NPC_ID, SOURCE_TEMPLATE_GUID, TEMPLATE_GUID,
                                    PatchValidationError, validate_patch)

ROOT=pathlib.Path(__file__).parents[1]
TOKEN="a"*32
VALUES={"voicePackId":3178345104,"presetId":1602195472,"hair":100818570,"beard":0,
 "hairColorId":2593349132,"beardColorId":2593349132,"skinColor":510686028,
 "eyeBrowColor":1294605571,"eyeColor":1843389514}

def key(n):
 import re
 return re.sub(r"(?<!^)(?=[A-Z])","_",n).lower()
def evidence(**changes):
 d={"format":FORMAT,"patch_version":"0.4.0","run_token":TOKEN,"patch_applied":"true",
 "template_guid":TEMPLATE_GUID,"source_guid":SOURCE_TEMPLATE_GUID,"npc_id":str(EXPECTED_NPC_ID),
 "faction":"PlayerAlly","source_unchanged":"true","hashkey32_extraction_method":"EML_MAPPED_STRUCT_VALUE_UINT32",
 "hashkey32_unsupported_fields":"","resource_created":"CONFIRMED","guid_registry_status":"NOT_REQUIRED",
 "template_lookup_available":"true","template_lookup_confirmed":"true","template_lookup_method":"EML_ASSET_MANAGER_GET_RESOURCE",
 "lookup_guid":TEMPLATE_GUID,"lookup_resource_type":"keen::ecs::TemplateResource","lookup_component_count":"81",
 "component_count":"81","fingerprint_hash":"1234abcd","lookup_fingerprint":"1234abcd",
 "components":"keen::ecs::CharacterSetup,keen::ecs::RenderEquipment,keen::ecs::AnimationGraphResourceComponent2,keen::ecs::ForceSave,keen::ecs::ActiveNpcState",
 "source_components":"keen::ecs::CharacterSetup,keen::ecs::RenderEquipment,keen::ecs::AnimationGraphResourceComponent2,keen::ecs::ForceSave,keen::ecs::ActiveNpcState",
 "character_setup_match":"true","animation_graph_guid":"g","source_animation_graph_guid":"g",
 "visual_references_match":"true","visual_dependencies_resolved":"true"}
 for n,v in VALUES.items():
  k=key(n)
  d.update({f"source_{k}_status":"CONFIRMED",f"source_{k}_type":"HashKey32",f"source_{k}_value":str(v),f"source_{k}_provenance":"SOURCE_EML_REFLECTION",
            f"clone_{k}_status":"CONFIRMED",f"clone_{k}_type":"HashKey32",f"clone_{k}_value":str(v),f"clone_{k}_provenance":"CLONE_EML_REFLECTION"})
 d.update(changes)
 return "\n".join(f"{k}={v}" for k,v in d.items())+"\n"
OBS={"writer_finalized":True,"run_token":TOKEN,"read_only":True,"spawn_forbidden":True,"bridge_available":True,"truncated":False}
GAME={"local_test_world_loaded":True,"resource_errors":[],"game_errors":[]}
INTEGRITY={"source_unchanged":True}

class HashKeyTests(unittest.TestCase):
 def test_01_valid(self): self.assertEqual(decode_hashkey32(42,"SOURCE_EML_REFLECTION")["status"],"CONFIRMED")
 def test_02_zero(self): self.assertEqual(decode_hashkey32(0,"SOURCE_EML_REFLECTION")["value"],0)
 def test_03_max(self): self.assertEqual(decode_hashkey32(UINT32_MAX,"CLONE_EML_REFLECTION")["value"],UINT32_MAX)
 def test_04_negative(self): self.assertEqual(decode_hashkey32(-1,"SOURCE_EML_REFLECTION")["status"],"INVALID")
 def test_05_overflow(self): self.assertEqual(decode_hashkey32(UINT32_MAX+1,"SOURCE_EML_REFLECTION")["status"],"INVALID")
 def test_06_nil(self): self.assertEqual(decode_hashkey32(None,"SOURCE_EML_REFLECTION")["status"],"MISSING")
 def test_07_userdata(self): self.assertEqual(decode_hashkey32(object(),"SOURCE_EML_REFLECTION")["status"],"UNSUPPORTED")
 def test_08_string(self): self.assertEqual(decode_hashkey32("42","SOURCE_EML_REFLECTION")["status"],"UNSUPPORTED")
 def test_09_equality(self): self.assertTrue(evaluate(evidence(),observer=OBS)["levels"]["H"])
 def test_10_mismatch(self): self.assertFalse(evaluate(evidence(clone_hair_value="1"),observer=OBS)["levels"]["H"])
 def test_11_missing(self): self.assertFalse(evaluate(evidence(clone_hair_status="MISSING",clone_hair_value=""),observer=OBS)["levels"]["H"])
 def test_12_unknown(self): self.assertFalse(evaluate(evidence(clone_hair_status="UNKNOWN"),observer=OBS)["levels"]["H"])
 def test_13_unsupported(self): self.assertFalse(evaluate(evidence(clone_hair_status="UNSUPPORTED"),observer=OBS)["levels"]["H"])
 def test_14_false_confirmed(self): self.assertFalse(evaluate(evidence(clone_hair_value="userdata: 0x1"),observer=OBS)["levels"]["H"])
 def test_15_kfc_mismatch(self): self.assertFalse(evaluate(evidence(clone_preset_id_value="7"),observer=OBS)["levels"]["H"])
 def test_16_missing_provenance(self): self.assertFalse(evaluate(evidence(clone_hair_provenance=""),observer=OBS)["levels"]["H"])
 def test_17_invalid_provenance(self): self.assertFalse(evaluate(evidence(clone_hair_provenance="KFC_CONSTANT"),observer=OBS)["levels"]["H"])

class RegistrationAndContractTests(unittest.TestCase):
 def reg(self,**kw): return evaluate(evidence(**kw),observer=OBS)
 def test_18_created_no_registry_allowed_when_not_required(self): self.assertTrue(self.reg()["levels"]["R"])
 def test_19_registry_without_lookup(self): self.assertFalse(self.reg(template_lookup_confirmed="false")["levels"]["R"])
 def test_20_lookup_unavailable(self): self.assertFalse(self.reg(template_lookup_available="false")["levels"]["R"])
 def test_21_guid_mismatch(self): self.assertFalse(self.reg(lookup_guid="bad")["levels"]["R"])
 def test_22_type_mismatch(self): self.assertFalse(self.reg(lookup_resource_type="x")["levels"]["R"])
 def test_23_fingerprint_mismatch(self): self.assertFalse(self.reg(lookup_fingerprint="bad")["levels"]["R"])
 def test_24_duplicate_guid(self):
  with self.assertRaisesRegex(PatchValidationError,"template_guid_conflict"):
   validate_patch(ROOT/"experimental/eml_humanoid",occupied_guids={TEMPLATE_GUID})
 def test_duplicate_evidence_key(self):
  with self.assertRaises(EvidenceV4Error): parse_evidence("a=1\na=2\n")
 def test_25_source_mutation(self): self.assertFalse(self.reg(source_unchanged="false")["levels"]["A"])
 def test_26_stale_token(self): self.assertFalse(self.reg(run_token="b"*32)["levels"]["A"])
 def test_27_writer_missing(self): self.assertFalse(evaluate(evidence())["levels"]["A"])
 def test_28_v3_compatibility(self): self.assertEqual(evaluate("format=aic_eml_humanoid_evidence_v3\n")["status"],"V3_COMPATIBILITY_ONLY")
 def test_29_v4_validation(self): self.assertEqual(parse_evidence(evidence())["format"],FORMAT)
 def test_30_gates_independent(self): self.assertEqual(set(self.reg()["levels"]),set("AHRVBC"))
 def test_31_spawn_false(self): self.assertFalse(evaluate(evidence(),observer=OBS,game_report=GAME,integrity=INTEGRITY)["spawn_ready"])
 def test_32_observer_read_only(self):
  s=(ROOT/"mods/aic_template_observer/main.lua").read_text(); self.assertIn("read_only=true",s)
 def test_33_observer_limit(self): self.assertIn("#encoded>1023",(ROOT/"mods/aic_template_observer/main.lua").read_text())
 def test_34_no_mutation_calls(self):
  s=(ROOT/"mods/aic_template_observer/main.lua").read_text()+ (ROOT/"experimental/eml_humanoid/src/mod.lua").read_text()
  for x in ("emf.spawn","emf.destroy","NpcCommandEvent","StartGuardingEvent"): self.assertNotIn(x,s)
 def test_35_phase_a_no_launcher(self):
  self.assertNotIn("subprocess",(ROOT/"companion/stage10_7.py").read_text())
 def test_all_nine_values_are_baseline_values(self): self.assertEqual(len(VALUES),9)
 def test_full_synthetic_success_is_not_spawn_ready(self):
  r=evaluate(evidence(),observer=OBS,game_report=GAME,integrity=INTEGRITY)
  self.assertEqual(r["status"],"LOAD_ONLY_SUCCESS"); self.assertFalse(r["spawn_ready"])

if __name__=="__main__": unittest.main()
