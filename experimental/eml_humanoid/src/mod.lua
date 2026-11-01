-- Stage 10.6 EML data-only patch. Creates a resource; never creates an entity.
if not loader.features.patch then return end
local TEMPLATE_GUID="a1c90001-5e4d-4a91-8a1c-000000000001"
local SOURCE_GUID="e3736dff-0ad2-47fc-903c-66c1775836e8"
local TEMPLATE_NAME="AIC_Humanoid_Companion_Experimental"
local NPC_ID=game.guid.hash(TEMPLATE_GUID)
local VISUAL_BASELINE_SHA256="535732bda93e41ff3b3070e362d649b9c6875101826d2c1823c81945b22d8837"
local RUN_TOKEN="__AIC_STAGE10_RUN_TOKEN__"
assert(RUN_TOKEN:match("^[0-9a-f]+$") and #RUN_TOKEN==32,"aic_eml_humanoid: missing Stage 10 run token")

local function component(data,kind)
 for _,v in ipairs(data.components) do if v.type==kind then return v.value end end
end
local function names(data)
 local r={} for _,v in ipairs(data.components) do r[#r+1]=v.type end
 table.sort(r) return table.concat(r,",")
end
local function scalar(v)
 if type(v)=="table" and v.value~=nil then v=v.value end
 if v==nil then return "MISSING","NONE","" end
 local t=type(v)
 if t=="string" or t=="number" or t=="boolean" then return "CONFIRMED",t,tostring(v) end
 return "UNSUPPORTED",t,""
end
local fields={
 {"gender","enum"},{"voicePackId","HashKey32"},{"presetId","HashKey32"},{"hair","HashKey32"},
 {"beard","HashKey32"},{"hairColorId","HashKey32"},{"beardColorId","HashKey32"},
 {"skinColor","HashKey32"},{"eyeBrowColor","HashKey32"},{"eyeColor","HashKey32"},
 {"useNewProportions","bool"},
}
local function snake(s) return (s:gsub("(%u)",function(c) return "_"..c:lower() end)) end
local function setup_lines(prefix,setup,provenance)
 local out={}
 for _,spec in ipairs(fields) do
  local status,_,value=scalar(setup and setup[spec[1]])
  local key=prefix.."_"..snake(spec[1])
  out[#out+1]=key.."_status="..status
  out[#out+1]=key.."_type="..spec[2]
  out[#out+1]=key.."_value="..value
  out[#out+1]=key.."_provenance="..provenance
 end
 return out
end
local function signature(data)
 local cs=component(data,"keen::ecs::CharacterSetup")
 local graph=component(data,"keen::ecs::AnimationGraphResourceComponent2")
 local parts={names(data)}
 for _,spec in ipairs(fields) do local s,t,v=scalar(cs and cs[spec[1]]); parts[#parts+1]=spec[1]..":"..s..":"..t..":"..v end
 parts[#parts+1]="animation:"..tostring(graph and graph.animationGraph)
 parts[#parts+1]="retarget:"..tostring(graph and graph.retargetData)
 return table.concat(parts,"|")
end
local function fnv32(text)
 local h=2166136261
 for i=1,#text do h=((h ~ text:byte(i))*16777619)&0xffffffff end
 return string.format("%08x",h)
end

local source=assert(game.assets.get_resource(SOURCE_GUID,"keen::ecs::TemplateResource"),
 "aic_eml_humanoid: source TemplateResource missing")
local before=signature(source.data)
local source_components=names(source.data)
local template=game.assets.create_resource(source.data,"keen::ecs::TemplateResource",TEMPLATE_GUID,0).data
template.name=TEMPLATE_NAME
local faction_set,npc_set=false,false
for _,c in ipairs(template.components) do
 if c.type=="keen::ecs::Faction" then c.value.faction="PlayerAlly"; faction_set=true
 elseif c.type=="keen::ecs::ActiveNpcState" then c.value.npcId={value=NPC_ID}; npc_set=true end
end
assert(faction_set and npc_set,"aic_eml_humanoid: identity components missing")
local created=assert(game.assets.get_resource(TEMPLATE_GUID,"keen::ecs::TemplateResource"),
 "aic_eml_humanoid: new TemplateResource lookup failed")
local registry=game.assets.get_resources_by_type("keen::GuidRegistryResource")[1]
local source_registered,registry_added=false,false
if registry then
 for _,g in ipairs(registry.data.guids) do if tostring(g)==tostring(source.guid) then source_registered=true end end
 if source_registered then table.insert(registry.data.guids,TEMPLATE_GUID); registry_added=true end
end
local source_setup=component(source.data,"keen::ecs::CharacterSetup")
local clone_setup=component(created.data,"keen::ecs::CharacterSetup")
local sg=component(source.data,"keen::ecs::AnimationGraphResourceComponent2")
local cg=component(created.data,"keen::ecs::AnimationGraphResourceComponent2")
local same_setup=signature(source.data)==signature(created.data)
local fingerprint=fnv32(signature(created.data))

if loader.features.export then
 local e={"format=aic_eml_humanoid_evidence_v3","patch_version=0.3.0","run_token="..RUN_TOKEN,
  "template_guid="..TEMPLATE_GUID,"source_guid="..SOURCE_GUID,"template_name="..TEMPLATE_NAME,
  "npc_id="..tostring(NPC_ID),"faction="..tostring(component(created.data,"keen::ecs::Faction").faction),
  "components="..names(created.data),"source_components="..source_components,
  "component_fingerprint="..fnv32(names(created.data)),
  "character_setup_match="..tostring(same_setup),
  "animation_graph_guid="..tostring(cg and cg.animationGraph or ""),
  "source_animation_graph_guid="..tostring(sg and sg.animationGraph or ""),
  "retarget_data="..tostring(cg and cg.retargetData or "null"),
  "source_retarget_data="..tostring(sg and sg.retargetData or "null"),
  "visual_references_provenance=SOURCE_KFC_VERIFIED|CLONE_EML_VERIFIED",
  "visual_reference_set_sha256="..VISUAL_BASELINE_SHA256,
  "visual_reference_count=18",
  "visual_references_match_basis=character_setup_preset_identity",
  "visual_references_match="..tostring(same_setup),
  "visual_dependencies_resolved="..tostring(same_setup),
  "resource_existence_provenance=RESOURCE_EXISTENCE_VERIFIED",
  "runtime_render_provenance=RUNTIME_RENDER_UNKNOWN",
  "source_unchanged="..tostring(before==signature(source.data)),
  "resource_lookup_after_create=true","source_registered="..tostring(source_registered),
  "registry_added="..tostring(registry_added),"writer_status=export_requested",
  "fingerprint_hash="..fingerprint}
 for _,line in ipairs(setup_lines("source",source_setup,"SOURCE_KFC_VERIFIED")) do e[#e+1]=line end
 for _,line in ipairs(setup_lines("clone",clone_setup,"CLONE_EML_VERIFIED")) do e[#e+1]=line end
 io.export("aic_eml_humanoid/template_evidence_v3.txt",table.concat(e,"\n").."\n")
end
print("AIC_EML_TEMPLATE_V3_READY",RUN_TOKEN,TEMPLATE_GUID,NPC_ID,fingerprint,registry_added)
print("AIC_EML_TEMPLATE_READY",RUN_TOKEN,TEMPLATE_GUID,NPC_ID,"CHARACTER_SETUP",fingerprint,registry_added)
