"""Stage 10.6 evidence v3 parser and load-only evaluator."""
from __future__ import annotations
import re
from typing import Any
from .eml_humanoid import TEMPLATE_GUID, SOURCE_TEMPLATE_GUID, EXPECTED_NPC_ID
from .visual_fingerprint import CHARACTER_SETUP_FIELDS, EVIDENCE_STATUSES
FORMAT="aic_eml_humanoid_evidence_v3"; RUN_TOKEN=re.compile(r"^[0-9a-f]{32}$")
VISUAL_BASELINE_SHA256="535732bda93e41ff3b3070e362d649b9c6875101826d2c1823c81945b22d8837"
REQUIRED_COMPONENTS={"keen::ecs::CharacterSetup","keen::ecs::RenderEquipment",
 "keen::ecs::AnimationGraphResourceComponent2","keen::ecs::ForceSave","keen::ecs::ActiveNpcState"}
class EvidenceV3Error(ValueError): pass
def parse_evidence(text):
    result={}
    for line in text.splitlines():
        if not line or "=" not in line: raise EvidenceV3Error("malformed_line")
        key,value=line.split("=",1)
        if not re.fullmatch(r"[a-z0-9_]+",key) or key in result: raise EvidenceV3Error("duplicate_or_invalid_key")
        result[key]=value
    return result
def _bool(v): return True if v=="true" else False if v=="false" else None
def _setup(e,prefix):
    result={}; valid=True
    for name in CHARACTER_SETUP_FIELDS:
        key=re.sub(r"(?<!^)(?=[A-Z])","_",name).lower()
        status=e.get(f"{prefix}_{key}_status","UNKNOWN"); typ=e.get(f"{prefix}_{key}_type","")
        value=e.get(f"{prefix}_{key}_value",""); provenance=e.get(f"{prefix}_{key}_provenance","")
        if status not in EVIDENCE_STATUSES or (status=="CONFIRMED" and (not typ or value=="")): valid=False
        result[name]={"status":status,"type":typ,"value":value,"provenance":provenance}
    return result,valid
def evaluate_visual_load(evidence_text, *, eml_log=None, observer=None, game_report=None, integrity=None):
    if evidence_text is None:
        return {"status":"NOT_EXECUTED","levels":{"A":None,"V":None,"B":None,"C":None},
         "load_only_success":False,"spawn_ready":False,"errors":[],"unknowns":["runtime_evidence_absent"]}
    try: e=parse_evidence(evidence_text)
    except EvidenceV3Error as exc:
        return {"status":"FAILED","levels":{"A":False,"V":False,"B":None,"C":None},
         "load_only_success":False,"spawn_ready":False,"errors":[str(exc)],"unknowns":[]}
    token=e.get("run_token"); components=set(filter(None,e.get("components","").split(",")))
    source_components=set(filter(None,e.get("source_components","").split(",")))
    ss,sv=_setup(e,"source"); cs,cv=_setup(e,"clone")
    setup_match=sv and cv and all(ss[n]["status"]==cs[n]["status"]=="CONFIRMED"
      and ss[n]["type"]==cs[n]["type"] and ss[n]["value"]==cs[n]["value"] for n in CHARACTER_SETUP_FIELDS)
    writer=bool(observer and observer.get("writer_finalized") is True and observer.get("run_token")==token)
    a={"format":e.get("format")==FORMAT,"run_token":bool(token and RUN_TOKEN.fullmatch(token)),
      "template_guid":e.get("template_guid")==TEMPLATE_GUID,"source_guid":e.get("source_guid")==SOURCE_TEMPLATE_GUID,
      "npc_id":e.get("npc_id")==str(EXPECTED_NPC_ID),"faction":e.get("faction")=="PlayerAlly",
      "source_unchanged":_bool(e.get("source_unchanged")) is True,"writer_finalized":writer}
    v={"structural":REQUIRED_COMPONENTS<=components and components==source_components,
      "character_setup":setup_match,"references":_bool(e.get("visual_references_match")) is True
       and e.get("visual_reference_set_sha256")==VISUAL_BASELINE_SHA256
       and e.get("visual_reference_count")=="18"
       and e.get("visual_references_match_basis")=="character_setup_preset_identity",
      "dependencies":_bool(e.get("visual_dependencies_resolved")) is True,
      "animation":e.get("animation_graph_guid")==e.get("source_animation_graph_guid") not in (None,""),
      "retarget":e.get("retarget_data")==e.get("source_retarget_data")}
    la,lv=all(a.values()),all(v.values())
    lb=None if game_report is None else all((game_report.get("main_menu_reached") is True,
      game_report.get("local_test_world_loaded") is True,game_report.get("resource_errors")==[],
      game_report.get("game_errors")==[],integrity is not None and integrity.get("source_unchanged") is True))
    lc=None if observer is None else all((observer.get("read_only") is True,observer.get("spawn_forbidden") is True,
      observer.get("run_token")==token,observer.get("fingerprint_hash")==e.get("fingerprint_hash")))
    errors=[f"{g}:{k}" for g,c in (("A",a),("V",v)) for k,val in c.items() if not val]
    unknowns=([] if lb is not None else ["game_load_not_evaluated"])+([] if lc is not None else ["observer_not_evaluated"])
    success=la and lv and lb is True and lc is True and not errors
    return {"status":"LOAD_ONLY_SUCCESS" if success else "FAILED","levels":{"A":la,"V":lv,"B":lb,"C":lc},
      "checks":{"A":a,"V":v},"load_only_success":success,"runtime_render_confirmed":None,
      "spawn_ready":False,"fingerprint_hash":e.get("fingerprint_hash"),"errors":errors,"unknowns":unknowns}
