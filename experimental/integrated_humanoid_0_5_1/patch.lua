-- Patch 0.5.1 library. Build-time resources only; no entity/runtime API.
local M = {}
local KIND = 'keen::ecs::TemplateResource'
local KEYS = {'beard','beardColorId','eyeBrowColor','eyeColor','hair','hairColorId','presetId','skinColor','voicePackId'}
local function need(ok, code) assert(ok, 'AIC_PATCH:'..code) end
-- Pinned vendor EML converter.rs: Guid/Reference -> Lua string, including
-- Guid::NONE -> 00000000-0000-0000-0000-000000000000. Optional(None) -> nil.
-- MappedStructValue is userdata; its reference field is NOT Guid userdata.
local ZERO='00000000-0000-0000-0000-000000000000'
local function reference(v,nullable)
 local t=type(v)
 if t=='nil' then
  if nullable then return 'null','LUA_NIL',nil end
  return nil,'LUA_NIL','MISMATCH'
 end
 if t~='string' then return nil,'UNSUPPORTED_NO_COERCION','UNSUPPORTED_TYPE' end
 if #v~=36 or not v:match('^%x%x%x%x%x%x%x%x%-%x%x%x%x%-%x%x%x%x%-%x%x%x%x%-%x%x%x%x%x%x%x%x%x%x%x%x$') then
  return nil,'STRING_INVALID_GUID','MISMATCH'
 end
 local s=v:lower()
 if s==ZERO then
  if nullable then return 'null','GUID_STRING_ZERO',nil end
  return nil,'GUID_STRING_ZERO','MISMATCH'
 end
 return s,'GUID_STRING',nil
end
local function safe(v)
 if type(v)=='string' then return v:sub(1,96):gsub('[^%w%-_.:]','?') end
 if v==nil then return 'nil' end
 return '<'..type(v)..'>' -- no userdata tostring/metamethod/pointer coercion
end
local function graph_check(graph,p,output)
 local errors={}
 -- Diagnose BOTH fields before any failure, without creating resource/evidence.
 for _,spec in ipairs({{'animationGraph',p.animation_graph,false,'ANIMATION_GRAPH'},
                      {'retargetData','null',true,'RETARGET_DATA'}}) do
  local ok,v=pcall(function() return graph[spec[1]] end)
  local value,method,err
  if ok then value,method,err=reference(v,spec[3])
  else method='FIELD_READ_FAILED';err='UNSUPPORTED_TYPE' end
  if not err and value~=spec[2] then err='MISMATCH' end
  output('AIC_GRAPH_DIAG_V1|'..p.run_token..'|'..spec[1]..
   '|container='..type(graph)..'|lua_type='..(ok and type(v) or 'unreadable')..
   '|read=field_index/value_to_lua|method='..method..'|actual='..(ok and safe(v) or 'unreadable')..
   '|normalized='..(value or 'INVALID')..'|expected='..spec[2]..'|result='..(err or 'PASS'))
  if err then errors[#errors+1]=spec[4]..'_'..err end
 end
 need(#errors==0,table.concat(errors,','))
end
local function required_guid(v,code)
 local value,_,err=reference(v,false);need(not err,code..'_'..(err or ''));return value
end
local function component(data, kind)
 local found
 for _, c in ipairs(data.components) do
  if c.type == kind then need(not found,'duplicate_component'); found=c.value end
 end
 return found
end
local function u32(v)
 local ok,n=pcall(function() return v.value end)
 need(ok and type(n)=='number' and n%1==0 and n>=0 and n<=4294967295,'HashKey32')
 return n
end
local function fnv(s)
 local h=2166136261
 for i=1,#s do h=((h ~ s:byte(i))*16777619)&0xffffffff end
 return string.format('%08x',h)
end
-- Deterministic comparison, not a cryptographic resource hash. Unknown userdata
-- fails closed; never stringify a userdata pointer and call it source integrity.
local function canonical(game,v,depth)
 depth=(depth or 0)+1; need(depth<96,'value_depth')
 local t=type(v)
 if t=='nil' then return 'nil' end
 if t=='string' then return 's'..#v..':'..v end
 if t=='number' then
  need(v==v and math.abs(v)~=math.huge,'nonfinite')
  return math.type(v)=='integer' and ('i'..tostring(v)) or ('n'..string.format('%.17g',v))
 end
 if t=='boolean' then return tostring(v) end
 need(t=='table' or t=='userdata','unsupported_value')
 local metadata=game.types.of(v)
 if metadata and (metadata.primitive_type=='BlobVariant' or metadata.primitive_type=='DsVariant') then
  return 'v'..canonical(game,v.type,depth)..canonical(game,v.value,depth)
 end
 local parts={}
 for k,item in pairs(v) do parts[#parts+1]=canonical(game,k,depth)..'='..canonical(game,item,depth) end
 table.sort(parts); return '{'..table.concat(parts,';')..'}'
end
local function names(data)
 local r={} for _,c in ipairs(data.components) do r[#r+1]=c.type end
 table.sort(r); return table.concat(r,',')
end
local function keys(setup)
 local r={} for _,k in ipairs(KEYS) do r[#r+1]=k..'='..string.format('%.0f',u32(setup[k])) end
 return table.concat(r,',')
end
local function emit(p,values,output)
 local sorted={} for k in pairs(values) do sorted[#sorted+1]=k end; table.sort(sorted)
 local body={}
 for _,k in ipairs(sorted) do
  local value=tostring(values[k]); need(not value:find('[\r\n|]'),'frame_value')
  body[#body+1]=k..'|'..value
 end
 local prefix='AIC_EVIDENCE_V8|'..p.run_token..'|'
 output(prefix..'BEGIN|'..#body)
 for _,line in ipairs(body) do output(prefix..line) end
 output(prefix..'END|'..fnv(table.concat(body,'\n')))
end
function M.run(game,loader,p,output)
 need(loader.features.patch==true,'patch_disabled')
 need(p.accepted_limited_baseline==true,'baseline_not_accepted')
 need(#p.run_token==32 and p.run_token:match('^[0-9a-f]+$'),'run_token')
 need(game.version==p.game_version,'UNSUPPORTED_GAME_BUILD')
 local faction=game.types.get('keen::FactionType')
 need(faction and faction.enum_fields.PlayerAlly.value==11,'faction_enum_changed')
 need(game.guid.hash(p.clone_guid)==p.npc_id,'npc_hash_changed')
 need(not game.assets.get_resource(p.clone_guid,KIND),'guid_collision')
 local source=assert(game.assets.get_resource(p.source_guid,KIND),'source_missing')
 need(#source.data.components==p.component_count and fnv(names(source.data))==p.component_fingerprint,'component_schema')
 local cs=assert(component(source.data,'keen::ecs::CharacterSetup'),'setup_missing')
 for _,k in ipairs(KEYS) do need(u32(cs[k])==p.hashkeys[k],'source_hashkey:'..k) end
 need(cs.gender==p.gender and cs.useNewProportions==p.use_new_proportions,'setup_changed')
 local graph=assert(component(source.data,'keen::ecs::AnimationGraphResourceComponent2'),'graph_missing')
 graph_check(graph,p,output)
 need(component(source.data,'keen::ecs::RenderEquipment')~=nil,'equipment_missing')
 for _,dep in ipairs(p.dependencies) do need(game.assets.get_resource(dep.guid,dep.type)~=nil,'dependency_missing:'..dep.guid) end
 local hierarchy=assert(game.assets.get_resource(p.hierarchy_guid,'keen::ModelHierarchyResource'),'hierarchy_missing').data
 need(required_guid(hierarchy.hierarchyId,'hierarchy_guid')==p.hierarchy_guid and hierarchy.jointCount==p.joint_count and #hierarchy.jointNames==p.joint_count,'skeleton_changed')
 local collection=assert(game.assets.get_resource(p.preset_collection_guid,'keen::CharacterPresetCollection'),'presets_missing').data
 local preset
 for _,candidate in ipairs(collection.presets) do
  if u32(candidate.presetId)==u32(cs.presetId) then need(not preset,'duplicate_preset'); preset=candidate end
 end
 need(preset~=nil,'preset_missing')
 local ref_count=0
 for _,ref in ipairs(p.visual_references) do
  need(required_guid(preset.references[ref.slot],'visual_reference:'..ref.slot)==ref.guid,'visual_reference_changed:'..ref.slot)
  need(game.assets.get_resource(ref.guid,ref.type)~=nil,'visual_resource_missing')
  ref_count=ref_count+1
 end
 local scan=game.assets.get_resources_by_type(KIND)
 need(#scan==p.template_count,'template_scan_count')
 for _,r in ipairs(scan) do
  local npc=component(r.data,'keen::ecs::ActiveNpcState')
  if npc then need(u32(npc.npcId)~=p.npc_id,'npc_collision') end
 end
 local before=canonical(game,source.data)
 local old_faction=canonical(game,component(source.data,'keen::ecs::Faction'))
 local created=game.assets.create_resource(source.data,KIND,p.clone_guid,0)
 local clone=created.data
 clone.name='AIC_Humanoid_Companion_Experimental'
 component(clone,'keen::ecs::Faction').faction='PlayerAlly'
 component(clone,'keen::ecs::ActiveNpcState').npcId={value=p.npc_id}
 local lookup=assert(game.assets.get_resource(p.clone_guid,KIND),'lookup_failed')
 need(required_guid(lookup.guid,'lookup_guid')==p.clone_guid and lookup.part==0,'lookup_identity')
 need(lookup.type.qualified_name==KIND,'lookup_type')
 need(canonical(game,source.data)==before,'source_mutated')
 need(canonical(game,component(source.data,'keen::ecs::Faction'))==old_faction,'source_faction_mutated')
 need(#lookup.data.components==#source.data.components and names(lookup.data)==names(source.data),'clone_components')
 -- Compare every reflected component field except the two deliberate overrides.
 for _,s in ipairs(source.data.components) do
  local c=assert(component(lookup.data,s.type),'clone_component_missing')
  if s.type=='keen::ecs::Faction' or s.type=='keen::ecs::ActiveNpcState' then
   local skip=s.type=='keen::ecs::Faction' and 'faction' or 'npcId'
   local a,b={},{}
   for k,v in pairs(s.value) do if k~=skip then a[k]=v end end
   for k,v in pairs(c) do if k~=skip then b[k]=v end end
   need(canonical(game,a)==canonical(game,b),'clone_field_changed:'..s.type)
  else need(canonical(game,s.value)==canonical(game,c),'clone_component_changed:'..s.type) end
 end
 need(component(clone,'keen::ecs::Faction').faction=='PlayerAlly','faction_assignment')
 need(u32(component(clone,'keen::ecs::ActiveNpcState').npcId)==p.npc_id,'npc_assignment')
 local ccs=component(lookup.data,'keen::ecs::CharacterSetup')
 emit(p,{schema='8',patch='0.5.1',build='1287369',owner='EMF_INTEGRATED',
  plan_id=p.plan_id,profile_sha256=p.profile_sha256,baseline_sha256=p.baseline_sha256,
  source_guid=source.guid,clone_guid=lookup.guid,resource_type=KIND,part='0',
  component_count=#clone.components,component_fingerprint=fnv(names(clone)),
  source_hashkeys=keys(cs),clone_hashkeys=keys(ccs),hashkey_provenance='EML_MAPPED_STRUCT_VALUE_UINT32',
  gender=ccs.gender,use_new_proportions=ccs.useNewProportions,
  animation_graph=required_guid(component(clone,'keen::ecs::AnimationGraphResourceComponent2').animationGraph,'clone_graph'),
  retarget_data='null',source_unchanged=true,source_comparison='FULL_REFLECTED_VALUE_EQUALITY',
  source_fnv32=fnv(before),clone_fields_preserved=true,render_equipment_preserved=true,
  dependencies_resolved=#p.dependencies,dependency_set_sha256=p.dependency_set_sha256,
  hierarchy_guid=required_guid(hierarchy.hierarchyId,'hierarchy_guid'),joint_count=hierarchy.jointCount,visual_reference_count=ref_count,
  visual_basis='PRESERVED_SOURCE_SETUP_AND_COMPONENTS_RESOURCE_EXISTENCE',
  resource_lookup='EML_APP_STATE_AFTER_CREATE',npc_id=u32(component(clone,'keen::ecs::ActiveNpcState').npcId),
  npc_collision_scan=#scan,faction=component(clone,'keen::ecs::Faction').faction,
  faction_enum_value=faction.enum_fields.PlayerAlly.value,
  writer_status='REQUESTED_NOT_FINALIZED',runtime_render='UNKNOWN',spawn_ready=false,errors='NONE'},output)
end
M.canonical=canonical; M.u32=u32; M.fnv=fnv
M.reference=reference; M.graph_check=graph_check
return M
