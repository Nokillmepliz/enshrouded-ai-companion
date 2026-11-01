import unittest
from pathlib import Path
from lupa import LuaRuntime
from companion.stage10_6 import evaluate_visual_load, parse_evidence, EvidenceV3Error
from companion.visual_fingerprint import (CHARACTER_SETUP_FIELDS, VISUAL_COMPONENTS,
    VisualFingerprintError, assess_visual_pair)

ROOT=Path(__file__).resolve().parents[1]
TOKEN="0123456789abcdef0123456789abcdef"
VALUES={"gender":("enum","Male"),"voicePackId":("HashKey32","3178345104"),
 "presetId":("HashKey32","1602195472"),"hair":("HashKey32","100818570"),
 "beard":("HashKey32","0"),"hairColorId":("HashKey32","2593349132"),
 "beardColorId":("HashKey32","2593349132"),"skinColor":("HashKey32","510686028"),
 "eyeBrowColor":("HashKey32","1294605571"),"eyeColor":("HashKey32","1843389514"),
 "useNewProportions":("bool","false")}
def snake(s):
 import re
 return re.sub(r"(?<!^)(?=[A-Z])","_",s).lower()
def evidence(**changes):
 components=sorted(set(VISUAL_COMPONENTS)|{"keen::ecs::ForceSave","keen::ecs::ActiveNpcState"})
 d={"format":"aic_eml_humanoid_evidence_v3","patch_version":"0.3.0","run_token":TOKEN,
  "template_guid":"a1c90001-5e4d-4a91-8a1c-000000000001",
  "source_guid":"e3736dff-0ad2-47fc-903c-66c1775836e8","npc_id":"2939921867",
  "faction":"PlayerAlly","components":",".join(components),"source_components":",".join(components),
  "character_setup_match":"true","animation_graph_guid":"402df515-5965-4b01-a17b-17d482a91af4",
  "source_animation_graph_guid":"402df515-5965-4b01-a17b-17d482a91af4",
  "retarget_data":"null","source_retarget_data":"null","visual_references_match":"true",
  "visual_reference_set_sha256":"535732bda93e41ff3b3070e362d649b9c6875101826d2c1823c81945b22d8837",
  "visual_reference_count":"18","visual_references_match_basis":"character_setup_preset_identity",
  "visual_dependencies_resolved":"true","source_unchanged":"true","fingerprint_hash":"deadbeef"}
 for field,(typ,value) in VALUES.items():
  for prefix,prov in (("source","SOURCE_KFC_VERIFIED"),("clone","CLONE_EML_VERIFIED")):
   k=f"{prefix}_{snake(field)}"; d[k+"_status"]="CONFIRMED"; d[k+"_type"]=typ
   d[k+"_value"]=value; d[k+"_provenance"]=prov
 d.update(changes)
 return "\n".join(f"{k}={v}" for k,v in d.items())+"\n"
def observer(**changes):
 d={"writer_finalized":True,"run_token":TOKEN,"read_only":True,"spawn_forbidden":True,
    "fingerprint_hash":"deadbeef"}; d.update(changes); return d
GAME={"main_menu_reached":True,"local_test_world_loaded":True,"resource_errors":[],"game_errors":[]}
INTEGRITY={"source_unchanged":True}

class EvidenceV3Tests(unittest.TestCase):
 def test_complete_contract_passes_a_v(self):
  r=evaluate_visual_load(evidence(),observer=observer())
  self.assertTrue(r["levels"]["A"]); self.assertTrue(r["levels"]["V"])
 def test_full_load_only_gate(self):
  r=evaluate_visual_load(evidence(),observer=observer(),game_report=GAME,integrity=INTEGRITY)
  self.assertEqual(r["status"],"LOAD_ONLY_SUCCESS"); self.assertFalse(r["spawn_ready"])
 def test_no_runtime_is_not_executed(self): self.assertEqual(evaluate_visual_load(None)["status"],"NOT_EXECUTED")
 def test_duplicate_key_rejected(self):
  with self.assertRaises(EvidenceV3Error): parse_evidence("format=x\nformat=y\n")
 def test_malformed_line_rejected(self):
  with self.assertRaises(EvidenceV3Error): parse_evidence("broken\n")
 def test_stale_token_fails(self): self.assertFalse(evaluate_visual_load(evidence(run_token="0"*32),observer=observer())["levels"]["A"])
 def test_bad_token_shape_fails(self): self.assertFalse(evaluate_visual_load(evidence(run_token="x"),observer=observer(run_token="x"))["levels"]["A"])
 def test_clone_guid_fails(self): self.assertFalse(evaluate_visual_load(evidence(template_guid="bad"),observer=observer())["levels"]["A"])
 def test_source_guid_fails(self): self.assertFalse(evaluate_visual_load(evidence(source_guid="bad"),observer=observer())["levels"]["A"])
 def test_npc_id_fails(self): self.assertFalse(evaluate_visual_load(evidence(npc_id="1"),observer=observer())["levels"]["A"])
 def test_faction_fails(self): self.assertFalse(evaluate_visual_load(evidence(faction="Vukah"),observer=observer())["levels"]["A"])
 def test_source_mutation_fails(self): self.assertFalse(evaluate_visual_load(evidence(source_unchanged="false"),observer=observer())["levels"]["A"])
 def test_writer_required(self): self.assertFalse(evaluate_visual_load(evidence())["levels"]["A"])
 def test_writer_token_correlated(self): self.assertFalse(evaluate_visual_load(evidence(),observer=observer(run_token="f"*32))["levels"]["A"])
 def test_component_loss_fails(self): self.assertFalse(evaluate_visual_load(evidence(components="keen::ecs::CharacterSetup"),observer=observer())["levels"]["V"])
 def test_component_mismatch_fails(self): self.assertFalse(evaluate_visual_load(evidence(source_components="x"),observer=observer())["levels"]["V"])
 def test_missing_setup_is_not_match(self): self.assertFalse(evaluate_visual_load(evidence(clone_hair_status="MISSING"),observer=observer())["levels"]["V"])
 def test_unknown_setup_is_not_match(self): self.assertFalse(evaluate_visual_load(evidence(clone_hair_status="UNKNOWN"),observer=observer())["levels"]["V"])
 def test_unsupported_setup_is_not_match(self): self.assertFalse(evaluate_visual_load(evidence(clone_hair_status="UNSUPPORTED"),observer=observer())["levels"]["V"])
 def test_setup_value_mismatch_fails(self): self.assertFalse(evaluate_visual_load(evidence(clone_hair_value="1"),observer=observer())["levels"]["V"])
 def test_setup_type_mismatch_fails(self): self.assertFalse(evaluate_visual_load(evidence(clone_hair_type="U64"),observer=observer())["levels"]["V"])
 def test_animation_mismatch_fails(self): self.assertFalse(evaluate_visual_load(evidence(animation_graph_guid="x"),observer=observer())["levels"]["V"])
 def test_retarget_mismatch_fails(self): self.assertFalse(evaluate_visual_load(evidence(retarget_data="x"),observer=observer())["levels"]["V"])
 def test_reference_mismatch_fails(self): self.assertFalse(evaluate_visual_load(evidence(visual_references_match="false"),observer=observer())["levels"]["V"])
 def test_dependency_unknown_fails(self): self.assertFalse(evaluate_visual_load(evidence(visual_dependencies_resolved="unknown"),observer=observer())["levels"]["V"])
 def test_game_errors_fail_b(self):
  bad=dict(GAME,game_errors=["x"]); self.assertFalse(evaluate_visual_load(evidence(),observer=observer(),game_report=bad,integrity=INTEGRITY)["levels"]["B"])
 def test_integrity_required_for_b(self): self.assertFalse(evaluate_visual_load(evidence(),observer=observer(),game_report=GAME)["levels"]["B"])
 def test_observer_hash_correlated(self): self.assertFalse(evaluate_visual_load(evidence(),observer=observer(fingerprint_hash="bad"))["levels"]["C"])
 def test_runtime_render_remains_unknown(self): self.assertIsNone(evaluate_visual_load(evidence(),observer=observer())["runtime_render_confirmed"])
 def test_parser_preserves_empty_value(self): self.assertEqual(parse_evidence("a=\n")["a"],"")

class VisualV2Tests(unittest.TestCase):
 def setup(self,value="x"):
  return {n:{"status":"CONFIRMED","type":VALUES[n][0],"value":VALUES[n][1]} for n in CHARACTER_SETUP_FIELDS}
 def template(self,**kw):
  d={"template_guid":"e3736dff-0ad2-47fc-903c-66c1775836e8","components":list(VISUAL_COMPONENTS),
    "character_setup":self.setup(),"resource_references_complete":False,"resource_references":[]}
  d.update(kw); return d
 def test_character_setup_level(self): self.assertTrue(assess_visual_pair(self.template(),self.template())["levels"]["CHARACTER_SETUP_MATCH"])
 def test_setup_schema_exact(self):
  with self.assertRaises(VisualFingerprintError): assess_visual_pair(self.template(character_setup={}),self.template())
 def test_empty_complete_references_rejected(self):
  with self.assertRaises(VisualFingerprintError): assess_visual_pair(self.template(resource_references_complete=True),self.template())
 def test_provenance_and_spawn_gate(self):
  r=assess_visual_pair(self.template(),self.template()); self.assertIn("RUNTIME_RENDER_UNKNOWN",r["provenance"]); self.assertFalse(r["spawn_ready"])

class ObserverSourceTests(unittest.TestCase):
 def test_patch_readme_matches_v3_contract(self):
  value=(ROOT/"experimental/eml_humanoid/README.md").read_text(encoding="utf-8")
  self.assertIn("patch **0.3.0**",value)
  self.assertIn("aic_eml_humanoid_evidence_v3",value)
  self.assertNotIn("версия patch 0.2.0",value)
 def test_tracked_baseline_hash_is_self_consistent(self):
  import hashlib,json
  value=json.loads((ROOT/"companion/data/hunter_visual_baseline.json").read_text())
  expected=value.pop("canonical_sha256")
  raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),expected)
  self.assertEqual(len(value["references"]),18)
 def test_compact_limit_guard(self): self.assertIn("#encoded>1023",(ROOT/"mods/aic_template_observer/main.lua").read_text())
 def test_no_mutation_api(self):
  s=(ROOT/"mods/aic_template_observer/main.lua").read_text()
  for x in ("emf.spawn","emf.destroy","emf.emit","world:set"): self.assertNotIn(x,s)
 def test_v3_path(self): self.assertIn("template_evidence_v3.txt",(ROOT/"mods/aic_template_observer/main.lua").read_text())
 def test_patch_has_no_spawn(self):
  s=(ROOT/"experimental/eml_humanoid/src/mod.lua").read_text(); self.assertNotIn("emf.spawn",s)
 def test_observer_compiles(self):
  src=(ROOT/"mods/aic_template_observer/main.lua").read_text().replace("__AIC_STAGE10_RUN_TOKEN__",TOKEN)
  LuaRuntime().execute("emf={command=function() end,log=function() end}\npackage.preload['json']=function() return {encode=function() return '{}' end} end\n"+src)

if __name__=="__main__": unittest.main()
